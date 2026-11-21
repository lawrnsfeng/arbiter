//! Network address configuration.

/// A host and port pair.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Addr {
    pub host: String,
    pub port: u32,
}

impl Addr {
    /// Builds an address from a host and a port.
    pub fn new(host: &str, port: u32) -> Self {
        Addr {
            host: host.to_string(),
            port,
        }
    }

    /// Renders the address as `host:port`.
    pub fn render(&self) -> String {
        format!("{}:{}", self.host, self.port)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn renders_host_and_port() {
        assert_eq!(Addr::new("localhost", 8080).render(), "localhost:8080");
    }
}
