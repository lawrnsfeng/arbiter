//! A fixed series of sensor samples.

#[derive(Debug, Clone, Default)]
pub struct Samples {
    values: Vec<f64>,
}

impl Samples {
    pub fn new(values: Vec<f64>) -> Self {
        Samples { values }
    }

    pub fn len(&self) -> usize {
        self.values.len()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }

    /// Returns sample `i`, or `None` when `i` is out of range.
    pub fn get(&self, i: usize) -> Option<f64> {
        self.values.get(i).copied()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn get_in_and_out_of_range() {
        let s = Samples::new(vec![1.0, 2.0]);
        assert_eq!(s.get(1), Some(2.0));
        assert_eq!(s.get(2), None);
        assert_eq!(s.len(), 2);
    }
}
