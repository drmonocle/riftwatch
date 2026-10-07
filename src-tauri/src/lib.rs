use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};

#[tauri::command]
fn start_window_drag(window: tauri::WebviewWindow) {
    let _ = window.start_dragging();
}

#[tauri::command]
fn show_ticker(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.show();
        let _ = w.set_focus();
    }
}

#[tauri::command]
fn hide_ticker(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.hide();
    }
}

#[tauri::command]
fn set_ticker_topmost(app: tauri::AppHandle, topmost: bool) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.set_always_on_top(topmost);
    }
}

#[tauri::command]
fn show_main(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

#[tauri::command]
fn quit_app(app: tauri::AppHandle) {
    app.exit(0);
}

#[tauri::command]
fn open_external_url(url: String) {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        let _ = std::process::Command::new("cmd")
            .args(["/c", "start", "", &url])
            .creation_flags(CREATE_NO_WINDOW)
            .spawn();
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = std::process::Command::new("xdg-open")
            .arg(&url)
            .spawn();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            show_ticker,
            hide_ticker,
            set_ticker_topmost,
            start_window_drag,
            show_main,
            quit_app,
            open_external_url
        ])
        .setup(|app| {
            let show_i = MenuItem::with_id(app, "show", "Open RiftWatch", true, None::<&str>)?;
            let hide_i = MenuItem::with_id(app, "hide", "Hide to Tray", true, None::<&str>)?;
            let sep1 = PredefinedMenuItem::separator(app)?;

            let nav_live = MenuItem::with_id(app, "nav_live", "🔴 Live Matches", true, None::<&str>)?;
            let nav_schedule = MenuItem::with_id(app, "nav_schedule", "📅 Schedule & Results", true, None::<&str>)?;
            let nav_stream = MenuItem::with_id(app, "nav_stream", "📺 24/7 Stream Marathon", true, None::<&str>)?;
            let nav_watchlist = MenuItem::with_id(app, "nav_watchlist", "⭐ Watchlist & Teams", true, None::<&str>)?;
            let nav_news = MenuItem::with_id(app, "nav_news", "📰 News & Intel", true, None::<&str>)?;
            let nav_settings = MenuItem::with_id(app, "nav_settings", "⚙ Settings", true, None::<&str>)?;
            let sep2 = PredefinedMenuItem::separator(app)?;

            let toggle_hud = MenuItem::with_id(app, "toggle_hud", "📌 Toggle Desktop HUD", true, None::<&str>)?;
            let sep3 = PredefinedMenuItem::separator(app)?;

            let stream_twitch = MenuItem::with_id(app, "stream_twitch", "▶ Watch 24/7 on Twitch", true, None::<&str>)?;
            let stream_youtube = MenuItem::with_id(app, "stream_youtube", "▶ Watch 24/7 on YouTube", true, None::<&str>)?;
            let stream_sched = MenuItem::with_id(app, "stream_sched", "🌐 Full Schedule (lolworlds.com)", true, None::<&str>)?;
            let kofi_support = MenuItem::with_id(app, "kofi_support", "☕ Support on Ko-fi", true, None::<&str>)?;
            let sep4 = PredefinedMenuItem::separator(app)?;

            let quit_i = MenuItem::with_id(app, "quit", "Quit RiftWatch", true, None::<&str>)?;

            let menu = Menu::with_items(
                app,
                &[
                    &show_i,
                    &hide_i,
                    &sep1,
                    &nav_live,
                    &nav_schedule,
                    &nav_stream,
                    &nav_watchlist,
                    &nav_news,
                    &nav_settings,
                    &sep2,
                    &toggle_hud,
                    &sep3,
                    &stream_twitch,
                    &stream_youtube,
                    &stream_sched,
                    &kofi_support,
                    &sep4,
                    &quit_i,
                ],
            )?;

            let tray_icon = match tauri::image::Image::from_bytes(include_bytes!("../icons/32x32.png")) {
                Ok(img) => Some(img),
                Err(_) => app.default_window_icon().cloned(),
            };

            let mut builder = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("RiftWatch - LoL Esports Companion")
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                        "hide" => {
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.hide();
                            }
                        }
                        "nav_live" | "nav_schedule" | "nav_stream" | "nav_watchlist" | "nav_news" | "nav_settings" => {
                            let tab = match event.id.as_ref() {
                                "nav_live" => "live",
                                "nav_schedule" => "schedule",
                                "nav_stream" => "stream",
                                "nav_watchlist" => "watchlist",
                                "nav_news" => "news",
                                "nav_settings" => "settings",
                                _ => "live",
                            };
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                                let _ = w.emit("navigate_tab", tab);
                            }
                        }
                        "toggle_hud" => {
                            if let Some(w) = app.get_webview_window("ticker") {
                                if w.is_visible().unwrap_or(false) {
                                    let _ = w.hide();
                                } else {
                                    let _ = w.show();
                                    let _ = w.set_focus();
                                }
                            }
                        }
                        "stream_twitch" => {
                            open_external_url("https://www.twitch.tv/LoLWorldChampionship".to_string());
                        }
                        "stream_youtube" => {
                            open_external_url("https://www.youtube.com/@LoLWorldChampionships/live".to_string());
                        }
                        "stream_sched" => {
                            open_external_url("https://lolworlds.com".to_string());
                        }
                        "kofi_support" => {
                            open_external_url("https://ko-fi.com/monocle".to_string());
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(w) = app.get_webview_window("main") {
                            if w.is_visible().unwrap_or(false) {
                                let _ = w.hide();
                            } else {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                    }
                });

            if let Some(icon) = tray_icon {
                builder = builder.icon(icon);
            }

            let _ = builder.build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
