//! Small text helpers.

/// Collapses runs of whitespace into single spaces and trims both ends.
pub fn squash_ws(s: &str) -> String {
    s.split_whitespace().collect::<Vec<_>>().join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn squashes_whitespace() {
        assert_eq!(squash_ws("  a \t b\n c "), "a b c");
    }
}
