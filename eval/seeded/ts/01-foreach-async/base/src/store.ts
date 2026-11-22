export interface Item {
  sku: string;
  qty: number;
}

/** In-memory item store with an async write path, like a database client. */
export class Store {
  #items = new Map<string, Item>();

  async save(item: Item): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 1));
    this.#items.set(item.sku, item);
  }

  get(sku: string): Item | undefined {
    return this.#items.get(sku);
  }

  size(): number {
    return this.#items.size;
  }
}
