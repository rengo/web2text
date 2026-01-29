export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchSites() {
    const res = await fetch(`${API_URL}/sites/`);
    return res.json();
}

export async function fetchFeed(since: string, siteId?: string) {
    let url = `${API_URL}/feed/new?since=${since}&limit=50`;
    if (siteId) {
        url += `&site_id=${siteId}`;
    }
    const res = await fetch(url);
    return res.json();
}

export async function createSite(site: any) {
    const res = await fetch(`${API_URL}/sites/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(site)
    });
    return res.json();
}

export async function toggleSite(id: string, enabled: boolean) {
    const res = await fetch(`${API_URL}/sites/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
    });
    return res.json();
}
