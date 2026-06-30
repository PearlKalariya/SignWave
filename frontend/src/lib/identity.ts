// Per-browser stable identity, persisted in localStorage.

const ID_KEY = "signwave_user_id";
const NAME_KEY = "signwave_user_name";

export function getUserId(): string {
  if (typeof window === "undefined") return "anon";
  let id = localStorage.getItem(ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(ID_KEY, id);
  }
  return id;
}

export function getUserName(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(NAME_KEY) || "";
}

export function setUserName(name: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(NAME_KEY, name);
}
