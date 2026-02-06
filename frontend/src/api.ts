export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9000';

export async function request(endpoint: string, options: RequestInit = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include'
    });

    if (response.status === 401) {
        // We don't reload here automatically to avoid infinite loops if checkAuth fails
        // But throwing allows the caller to handle it
        throw new Error("Unauthorized");
    }

    return response;
}

export async function login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    // Login endpoint sets the cookie
    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });

    if (!res.ok) {
        throw new Error('Login failed');
    }
    return res.json();
}

export async function logout() {
    await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
    });
}

export async function checkAuth() {
    try {
        const res = await request('/auth/me');
        if (res.ok) {
            return await res.json();
        }
        return null;
    } catch (e) {
        return null;
    }
}

export async function fetchSites() {
    const res = await request('/sites/');
    return res.json();
}

export async function fetchFeed(since: string, siteId?: string, page: number = 1, pageSize: number = 50) {
    let url = `/feed/new?since=${since}&page=${page}&page_size=${pageSize}`;
    if (siteId) {
        url += `&site_id=${siteId}`;
    }
    const res = await request(url);
    return res.json();
}

export async function createSite(site: any) {
    const res = await request('/sites/', {
        method: 'POST',
        body: JSON.stringify(site)
    });
    return res.json();
}

export async function updateSite(id: string, update: any) {
    const res = await request(`/sites/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(update)
    });
    return res.json();
}

export async function toggleSite(id: string, enabled: boolean) {
    return updateSite(id, { enabled });
}

export async function fetchSettings() {
    const res = await request('/settings/');
    return res.json();
}

export async function updateSetting(key: string, value: string) {
    const res = await request(`/settings/${key}`, {
        method: 'PUT',
        body: JSON.stringify({ value })
    });
    return res.json();
}
