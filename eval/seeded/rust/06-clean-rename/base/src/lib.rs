//! Basic descriptive statistics.

/// Arithmetic mean of `xs`, or `None` for an empty slice.
pub fn calc_avg(xs: &[f64]) -> Option<f64> {
    if xs.is_empty() {
        return None;
    }
    Some(xs.iter().sum::<f64>() / xs.len() as f64)
}

/// Largest value in `xs`, or `None` for an empty slice.
pub fn max(xs: &[f64]) -> Option<f64> {
    xs.iter().copied().reduce(f64::max)
}

/// Spread between the largest and smallest values.
pub fn range(xs: &[f64]) -> Option<f64> {
    let min = xs.iter().copied().reduce(f64::min)?;
    Some(max(xs)? - min)
}

/// Mean absolute deviation from the mean.
pub fn mean_abs_dev(xs: &[f64]) -> Option<f64> {
    let m = calc_avg(xs)?;
    let devs: Vec<f64> = xs.iter().map(|x| (x - m).abs()).collect();
    calc_avg(&devs)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn avg_of_values() {
        assert_eq!(calc_avg(&[1.0, 2.0, 3.0]), Some(2.0));
        assert_eq!(calc_avg(&[]), None);
    }

    #[test]
    fn range_and_mad() {
        assert_eq!(range(&[4.0, 1.0, 3.0]), Some(3.0));
        assert_eq!(mean_abs_dev(&[1.0, 3.0]), Some(1.0));
    }
}
