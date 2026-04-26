// Prevents an extra console window from appearing in release builds on Windows
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    recap_lib::run()
}
