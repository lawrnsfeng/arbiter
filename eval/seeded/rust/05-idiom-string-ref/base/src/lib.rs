//! Stock inventory records.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Item {
    pub name: String,
    pub qty: u32,
}

impl Item {
    pub fn new(name: &str, qty: u32) -> Self {
        Item {
            name: name.to_string(),
            qty,
        }
    }
}

/// Total quantity across all items.
pub fn total_qty(items: &[Item]) -> u32 {
    items.iter().map(|i| i.qty).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sums_quantities() {
        let items = [Item::new("bolt", 3), Item::new("nut", 4)];
        assert_eq!(total_qty(&items), 7);
    }
}
