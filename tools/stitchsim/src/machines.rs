//! Machine profiles: the hard limits of the machine a file is meant for. `--machine`
//! picks one (default `brother-home`); the analyser flags stitches longer than the
//! machine sews, more stitches than it loads, and more colour changes than it holds.
//!
//! Sources: Brother home machines (PE/SE/NV series) refuse patterns over 500,000
//! stitches (Brother operation manuals, "maximum stitches per pattern"). The 12.1 mm
//! stitch limit is DST's ternary encoding (+-121 units of 0.1 mm), which every
//! commercial (Tajima-compatible) head shares and cadkit's writers split to. The rest
//! are ASSUMPTIONS, chosen conservatively until a manual says otherwise: Brother's 127
//! colour changes (the PEC colour list is indexed by a signed byte), Janome's and
//! Bernina's 12.7 mm (one signed byte of 0.1 mm in JEF / EXP), their 500,000 stitches
//! and 99 colour changes, and Tajima's 1,000,000 stitches and 999 changes (the DST
//! header's `CO` field has 3 digits).

#[derive(Clone, Copy, Debug)]
pub struct Profile {
    pub name: &'static str,
    pub label: &'static str,
    /// longest stitch the machine sews, mm
    pub max_stitch: f32,
    /// most needle penetrations in one pattern
    pub max_stitches: usize,
    /// most colour changes (colour blocks - 1)
    pub max_changes: usize,
}

pub const PROFILES: [Profile; 4] = [
    Profile { name: "brother-home", label: "Brother home (PE/SE/NV)", max_stitch: 12.1, max_stitches: 500_000, max_changes: 127 },
    Profile { name: "janome", label: "Janome (MC/MB)", max_stitch: 12.7, max_stitches: 500_000, max_changes: 99 },
    Profile { name: "tajima", label: "Tajima / commercial (DST)", max_stitch: 12.1, max_stitches: 1_000_000, max_changes: 999 },
    Profile { name: "bernina", label: "Bernina", max_stitch: 12.7, max_stitches: 500_000, max_changes: 99 },
];

pub fn find(name: &str) -> Option<usize> {
    PROFILES.iter().position(|p| p.name == name)
}
