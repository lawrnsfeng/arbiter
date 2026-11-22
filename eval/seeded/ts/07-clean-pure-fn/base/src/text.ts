/** Lower-cases text and joins its words with hyphens, for use in URLs. */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean)
    .join("-");
}
