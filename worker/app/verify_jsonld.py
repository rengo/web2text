
import asyncio
import httpx
from worker.app.scraper import ScraperEngine

async def verify_url(engine, url, expected_valid: bool):
    print(f"Checking {url}...")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"❌ Error fetching {url}: HTTP {resp.status_code}")
                return

            html = resp.text
            is_valid = engine._is_valid_article(html)
            
            status = "✅" if is_valid == expected_valid else "❌"
            result_str = "VALID ARTICLE" if is_valid else "NOT AN ARTICLE"
            expected_str = "VALID" if expected_valid else "INVALID"
            
            print(f"{status} {result_str} (Expected: {expected_str})")
    except Exception as e:
        print(f"❌ Exception checking {url}: {e}")

async def main():
    engine = ScraperEngine()
    
    test_cases = [
        # LM Neuquén
        ("https://www.lmneuquen.com/neuquen", False), # Category
        ("https://www.lmneuquen.com/neuquen/de-lit-killah-una-casa-regalo-las-sorpresas-que-trae-la-fiesta-la-confluencia-2026-n1226662", True), # Article

        # Clarín
        ("https://www.clarin.com/tema/politica.html", False), # Category/Theme
        ("https://www.clarin.com/politica/javier-milei-medidas-vivo-circo-oportunismo-funcionario-kicillof-contesto-bullrich-edad-imputabilidad_0_2KZP9Ozzvh.html", True), # Article

        # Río Negro
        ("https://www.rionegro.com.ar/economia/", False), # Category
        ("https://www.rionegro.com.ar/economia/nuevo-vencimiento-el-gobierno-se-prepara-para-pagar-us-878-millones-al-fmi-con-apoyo-del-tesoro-de-ee-uu-4453882/", True), # Article
    ]

    print("--- Starting JSON-LD Verification ---")
    for url, expected in test_cases:
        await verify_url(engine, url, expected)
    print("--- Verification Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
