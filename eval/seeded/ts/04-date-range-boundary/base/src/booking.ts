export interface Booking {
  id: string;
  /** Calendar day in ISO form, YYYY-MM-DD. */
  day: string;
  guests: number;
}

/** Total guests across the given bookings. */
export function totalGuests(bookings: Booking[]): number {
  return bookings.reduce((sum, b) => sum + b.guests, 0);
}
