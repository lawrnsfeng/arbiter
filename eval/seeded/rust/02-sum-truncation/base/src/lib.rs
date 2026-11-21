//! Length-prefixed frame encoding.
//!
//! Layout: `MAGIC` (1 byte), kind (1 byte), payload length (u16, big endian), payload.

use std::fmt;

pub const MAGIC: u8 = 0xF7;
pub const HEADER_LEN: usize = 4;

#[derive(Debug, PartialEq, Eq)]
pub enum FrameError {
    TooLarge(usize),
}

impl fmt::Display for FrameError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FrameError::TooLarge(n) => write!(f, "payload of {n} bytes exceeds u16::MAX"),
        }
    }
}

impl std::error::Error for FrameError {}

/// Encodes one frame. Fails if the payload does not fit the u16 length field.
pub fn encode(kind: u8, payload: &[u8]) -> Result<Vec<u8>, FrameError> {
    let len = u16::try_from(payload.len()).map_err(|_| FrameError::TooLarge(payload.len()))?;
    let mut out = Vec::with_capacity(HEADER_LEN + payload.len());
    out.push(MAGIC);
    out.push(kind);
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}

/// Returns the payload length written in a frame header, if the header is complete.
pub fn declared_len(frame: &[u8]) -> Option<u16> {
    match frame {
        [MAGIC, _, hi, lo, ..] => Some(u16::from_be_bytes([*hi, *lo])),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encodes_header_and_payload() {
        let f = encode(2, b"abc").unwrap();
        assert_eq!(f, vec![MAGIC, 2, 0, 3, b'a', b'b', b'c']);
        assert_eq!(declared_len(&f), Some(3));
    }

    #[test]
    fn rejects_oversized_payload() {
        let big = vec![0u8; 70_000];
        assert_eq!(encode(1, &big), Err(FrameError::TooLarge(70_000)));
    }
}
