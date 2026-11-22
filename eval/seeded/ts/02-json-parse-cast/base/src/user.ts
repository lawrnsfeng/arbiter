export interface User {
  id: number;
  name: string;
  email: string;
  role: "member" | "admin";
}

export function displayName(user: User): string {
  return `${user.name} <${user.email}>`;
}
