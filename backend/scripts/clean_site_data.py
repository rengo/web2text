import asyncio
import sys
import os
import uuid
from sqlalchemy import select, delete

# Add project root to sys.path to allow imports from shared
# Assumes script is located at <project_root>/backend/scripts/clean_site_data.py
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../..")) # go up backend/scripts -> root
# However, if running from root via `python backend/scripts/...`, cwd might be root.
# Let's just add the current working directory and the parent of the backend directory if needed.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

# If running inside docker container where WORKDIR is /app (parent of backend), logic might differ.
# Safer approach: try import, if fail, try adding paths.
try:
    from shared.core.database import AsyncSessionLocal
    from shared.core.models import Page, PageContent, Site
except ImportError:
    # Try adding the parent directory of 'backend' (which is root or /app)
    # script is in backend/scripts/. Parent is backend. Parent of backend is root.
    sys.path.append(os.path.abspath(os.path.join(current_dir, "../..")))
    try:
        from shared.core.database import AsyncSessionLocal
        from shared.core.models import Page, PageContent, Site
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please run this script from the project root (e.g. `python3 backend/scripts/clean_site_data.py`)")
        sys.exit(1)

async def clean_site_data(site_id_str: str, force: bool = False):
    try:
        site_id = uuid.UUID(site_id_str)
    except ValueError:
        print(f"Error: Invalid site ID format: {site_id_str}")
        return

    async with AsyncSessionLocal() as session:
        # Check if site exists
        result = await session.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        
        if not site:
            print(f"Warning: Site with ID {site_id} not found.")
            if not force:
                confirm = input("Do you want to proceed with deletion anyway? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Operation cancelled.")
                    return
        else:
            print(f"Found site: {site.name}")
            print(f"Base URL: {site.base_url}")
            
            if not force:
                confirm = input(f"Are you sure you want to delete ALL pages and content for this site? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Operation cancelled.")
                    return

        print(f"Deleting data for site {site_id}...")

        # Delete PageContents first (referencing pages)
        # We delete PageContents where the associated page belongs to the site
        stmt_contents = delete(PageContent).where(
            PageContent.page_id.in_(
                select(Page.id).where(Page.site_id == site_id)
            )
        )
        result_contents = await session.execute(stmt_contents)
        print(f"Deleted {result_contents.rowcount} page content entries.")

        # Delete Pages
        stmt_pages = delete(Page).where(Page.site_id == site_id)
        result_pages = await session.execute(stmt_pages)
        print(f"Deleted {result_pages.rowcount} pages.")

        await session.commit()
        print("Deletion complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 backend/scripts/clean_site_data.py <site_id> [--force]")
        sys.exit(1)
    
    site_id_arg = sys.argv[1]
    
    # Handle flag anywhere
    force_arg = False
    clean_args = []
    for arg in sys.argv[1:]:
        if arg == "--force":
            force_arg = True
        else:
            clean_args.append(arg)
            
    if not clean_args:
        print("Error: Missing site_id")
        sys.exit(1)
        
    site_id_arg = clean_args[0]
    
    try:
        asyncio.run(clean_site_data(site_id_arg, force_arg))
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
