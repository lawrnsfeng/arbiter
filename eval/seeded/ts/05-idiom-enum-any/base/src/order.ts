export interface Order {
  id: string;
  lines: { price: number; qty: number }[];
}

export function orderTotal(order: Order): number {
  return order.lines.reduce((sum, l) => sum + l.price * l.qty, 0);
}
