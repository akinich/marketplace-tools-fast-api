// src/api/client.ts
export const API_BASE_URL =
    process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

async function request<TResponse>(
    path: string,
    options: RequestInit = {}
): Promise<TResponse> {
    const res = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
    }

    return res.json() as Promise<TResponse>;
}

export const apiClient = {
    get: <T>(path: string) => request<T>(path),
    post: <T>(path: string, body: unknown) =>
        request<T>(path, {
            method: "POST",
            body: JSON.stringify(body),
        }),
};
