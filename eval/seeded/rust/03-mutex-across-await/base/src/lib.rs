//! A small shared cache for values loaded by async fetchers.

use std::collections::HashMap;
use std::future::Future;
use std::sync::Mutex;

#[derive(Default)]
pub struct Cache {
    inner: Mutex<HashMap<String, String>>,
}

impl Cache {
    pub fn new() -> Self {
        Self::default()
    }

    /// Returns the cached value for `key`, if any.
    pub fn get(&self, key: &str) -> Option<String> {
        self.inner.lock().unwrap().get(key).cloned()
    }

    /// Re-fetches `key` and stores the fresh value.
    pub async fn refresh<F, Fut>(&self, key: &str, fetch: F) -> String
    where
        F: FnOnce() -> Fut,
        Fut: Future<Output = String>,
    {
        let value = fetch().await;
        self.inner
            .lock()
            .unwrap()
            .insert(key.to_string(), value.clone());
        value
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn refresh_stores_value() {
        let cache = Cache::new();
        let v = cache.refresh("a", || async { "1".to_string() }).await;
        assert_eq!(v, "1");
        assert_eq!(cache.get("a").as_deref(), Some("1"));
    }
}
