import time
from collections import deque

import cv2
import numpy as np
import pyautogui

TARGET_FPS = 30
MIN_AREA = 800
COOLDOWN = 2.2
HISTORY_SIZE = 5
MIN_VOTES = 3
GRID_INTERVAL = 40

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02


def blend_overlay(base, overlay, alpha):
    """Blend an overlay onto the base frame with the given alpha."""
    cv2.addWeighted(overlay, alpha, base, 1.0 - alpha, 0, base)


def draw_jarvis_grid(frame):
    """Draw a subtle futuristic grid overlay across the frame."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    grid_color = (12, 24, 40)
    for x in range(0, w, GRID_INTERVAL):
        cv2.line(overlay, (x, 0), (x, h), grid_color, 1, cv2.LINE_AA)
    for y in range(0, h, GRID_INTERVAL):
        cv2.line(overlay, (0, y), (w, y), grid_color, 1, cv2.LINE_AA)
    cv2.line(overlay, (w // 2, 0), (w // 2, h), (10, 30, 55), 1, cv2.LINE_AA)
    cv2.line(overlay, (0, h // 2), (w, h // 2), (10, 30, 55), 1, cv2.LINE_AA)
    blend_overlay(frame, overlay, 0.09)


def draw_hud_panel(frame, display_gesture, finger_count, ready, cooldown, now):
    """Draw the right-side sci-fi telemetry HUD panel."""
    h, w = frame.shape[:2]
    panel_w = 320
    panel_h = 170
    panel_x = w - panel_w - 20
    panel_y = 20
    overlay = frame.copy()
    cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (6, 16, 28), -1)
    blend_overlay(frame, overlay, 0.42)

    accent = (150, 255, 255)
    accent_soft = (120, 210, 255)
    border = (80, 180, 255)

    cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), accent, 1, cv2.LINE_AA)
    cv2.line(frame, (panel_x + 10, panel_y + 36), (panel_x + panel_w - 10, panel_y + 36), accent, 1, cv2.LINE_AA)
    cv2.line(frame, (panel_x + 10, panel_y + 72), (panel_x + panel_w - 10, panel_y + 72), accent_soft, 1, cv2.LINE_AA)

    title_font = cv2.FONT_HERSHEY_DUPLEX
    content_font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(frame, 'J.A.R.V.I.S.', (panel_x + 14, panel_y + 30), title_font, 0.7, accent, 1, cv2.LINE_AA)
    cv2.putText(frame, f'GESTURE: {display_gesture}', (panel_x + 14, panel_y + 60), content_font, 0.55, accent_soft, 1, cv2.LINE_AA)
    cv2.putText(frame, f'FINGERS: {finger_count}', (panel_x + 14, panel_y + 88), content_font, 0.55, accent, 1, cv2.LINE_AA)

    status_text = 'READY' if ready else f'COOLDOWN {cooldown:.1f}s'
    status_color = accent if ready else border
    cv2.putText(frame, f'STATUS: {status_text}', (panel_x + 14, panel_y + 116), content_font, 0.55, status_color, 1, cv2.LINE_AA)

    bar_x = panel_x + 14
    bar_y = panel_y + 132
    bar_w = panel_w - 28
    bar_h = 10
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (18, 30, 48), -1)
    fill = int(bar_w * (1.0 if ready else max(0.0, 1.0 - cooldown / COOLDOWN)))
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill, bar_y + bar_h), accent, -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), accent_soft, 1, cv2.LINE_AA)

    pulse_strength = 0.4 + 0.1 * np.sin(now * 3.0)
    overlay2 = frame.copy()
    cv2.putText(overlay2, 'SYSTEM ACTIVE', (panel_x + 14, panel_y + panel_h - 10), content_font, 0.5, accent, 1, cv2.LINE_AA)
    blend_overlay(frame, overlay2, pulse_strength * 0.22)


def draw_target_reticle(frame, bbox, center, now):
    """Draw corner brackets and rotating rings around the detected hand."""
    if bbox is None or center is None:
        return

    bx, by, bw, bh = bbox
    cx, cy = center
    accent = (150, 255, 255)
    accent_soft = (100, 180, 255)
    ring_color = (120, 220, 255)

    # corner reticle brackets at bounding box corners
    length = 30
    thickness = 2
    cv2.line(frame, (bx, by), (bx + length, by), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx, by), (bx, by + length), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx + bw, by), (bx + bw - length, by), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx + bw, by), (bx + bw, by + length), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx, by + bh), (bx + length, by + bh), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx, by + bh), (bx, by + bh - length), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx + bw, by + bh), (bx + bw - length, by + bh), accent, thickness, cv2.LINE_AA)
    cv2.line(frame, (bx + bw, by + bh), (bx + bw, by + bh - length), accent, thickness, cv2.LINE_AA)

    # main center marker
    cv2.circle(frame, (cx, cy), 6, ring_color, 2, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), 3, accent, -1, cv2.LINE_AA)

    # rotating ring animation
    ring_base = int(min(bw, bh) * 0.75)
    ring1 = ring_base + int(6 * np.sin(now * 2.2))
    ring2 = ring_base + 26
    ring3 = ring_base + 46
    angle1 = int(now * 40) % 360
    angle2 = int(now * -28) % 360
    angle3 = int(now * 18) % 360

    overlay = frame.copy()
    cv2.circle(overlay, (cx, cy), ring1, accent_soft, 1, cv2.LINE_AA)
    cv2.ellipse(overlay, (cx, cy), (ring2, ring2), angle1, 0, 100, accent, 1, cv2.LINE_AA)
    cv2.ellipse(overlay, (cx, cy), (ring3, ring3), angle2, 180, 300, ring_color, 1, cv2.LINE_AA)
    cv2.line(overlay, (cx, cy - ring2), (cx, cy - ring2 + 18), accent_soft, 1, cv2.LINE_AA)
    cv2.line(overlay, (cx + ring2, cy), (cx + ring2 - 18, cy), accent_soft, 1, cv2.LINE_AA)
    blend_overlay(frame, overlay, 0.55)

    # pulsing outer glow ring
    glow_radius = ring1 + 18 + int(4 * np.sin(now * 3.7))
    cv2.circle(frame, (cx, cy), glow_radius, (80, 180, 255), 1, cv2.LINE_AA)


def draw_scanning_line(frame, bbox, now):
    """Draw a sweep line across the detected hand box."""
    if bbox is None:
        return
    bx, by, bw, bh = bbox
    scan_fraction = (np.sin(now * 3.0) * 0.5) + 0.5
    scan_y = int(by + scan_fraction * bh)
    overlay = frame.copy()
    cv2.line(overlay, (bx, scan_y), (bx + bw, scan_y), (110, 240, 255), 2, cv2.LINE_AA)
    for offset in (4, 8):
        alpha = 0.12 if offset == 4 else 0.08
        cv2.line(overlay, (bx, scan_y + offset), (bx + bw, scan_y + offset), (95, 210, 255), 1, cv2.LINE_AA)
    blend_overlay(frame, overlay, 0.35)


def draw_status_text(frame, bbox, state_text, now):
    """Draw a small floating readout near the hand."""
    if bbox is None:
        return
    bx, by, bw, bh = bbox
    text_x = bx
    text_y = max(20, by - 40)
    accent = (150, 255, 255)
    secondary = (100, 190, 255)
    font = cv2.FONT_HERSHEY_SIMPLEX

    overlay = frame.copy()
    cv2.putText(overlay, f'MODE: {state_text}', (text_x, text_y), font, 0.5, secondary, 1, cv2.LINE_AA)
    cv2.putText(overlay, f'ACTIVE', (text_x, text_y + 18), font, 0.5, accent, 1, cv2.LINE_AA)
    blend_overlay(frame, overlay, 0.28)


try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print('Webcam could not be opened. Please check your camera connection.')
        raise SystemExit(0)

    show_windows = True
    try:
        cv2.startWindowThread()
        cv2.namedWindow('JARVIS Gesture Control', cv2.WINDOW_NORMAL)
        cv2.moveWindow('JARVIS Gesture Control', 80, 80)
        cv2.resizeWindow('JARVIS Gesture Control', 1040, 720)
        cv2.namedWindow('Mask', cv2.WINDOW_NORMAL)
        cv2.moveWindow('Mask', 1140, 80)
        cv2.resizeWindow('Mask', 320, 240)
    except cv2.error as exc:
        print(f'Camera windows could not be created: {exc}')
        show_windows = False

    for name, val, maxv in [
        ('Low H', 0, 179), ('High H', 20, 179),
        ('Low S', 40, 255), ('High S', 255, 255),
        ('Low V', 40, 255), ('High V', 255, 255),
    ]:
        if show_windows:
            cv2.createTrackbar(name, 'JARVIS Gesture Control', val, maxv, lambda x: None)

    last_action_time = 0.0
    gesture_history = deque(maxlen=HISTORY_SIZE)
    prev_center = None
    state_text = 'SEARCHING'

    while True:
        start = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            print('Camera frame read failed.')
            break

        frame = cv2.flip(frame, 1)

        if show_windows:
            low = np.array([
                cv2.getTrackbarPos('Low H', 'JARVIS Gesture Control'),
                cv2.getTrackbarPos('Low S', 'JARVIS Gesture Control'),
                cv2.getTrackbarPos('Low V', 'JARVIS Gesture Control'),
            ], np.uint8)
            high = np.array([
                cv2.getTrackbarPos('High H', 'JARVIS Gesture Control'),
                cv2.getTrackbarPos('High S', 'JARVIS Gesture Control'),
                cv2.getTrackbarPos('High V', 'JARVIS Gesture Control'),
            ], np.uint8)
        else:
            low = np.array([0, 40, 40], np.uint8)
            high = np.array([20, 255, 255], np.uint8)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, low, high)
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frame_gesture = 'NONE'
        center = None
        bbox = None
        finger_count = 0

        if contours:
            hand = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(hand)
            if area > MIN_AREA:
                M = cv2.moments(hand)
                if M['m00']:
                    center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
                bbox = cv2.boundingRect(hand)
                if show_windows:
                    cv2.drawContours(frame, [hand], -1, (80, 255, 220), 2, cv2.LINE_AA)

                hull = cv2.convexHull(hand, returnPoints=False)
                hull_area = cv2.contourArea(cv2.convexHull(hand, returnPoints=True)) if len(hull) > 3 else 0
                solidity = float(area) / hull_area if hull_area > 0 else 0.0

                defects = None
                if hull is not None and len(hull) > 3:
                    defects = cv2.convexityDefects(hand, hull)

                defect_count = 0
                if defects is not None:
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        if d > 12000:
                            defect_count += 1
                            if show_windows:
                                far_pt = tuple(hand[f][0])
                                cv2.circle(frame, far_pt, 4, (0, 200, 255), -1, cv2.LINE_AA)

                finger_count = defect_count + 1 if defect_count > 0 else 0
                if defect_count >= 2 and solidity > 0.35:
                    frame_gesture = 'OPEN'
                elif defect_count <= 1 and solidity > 0.55:
                    frame_gesture = 'FIST'
                else:
                    frame_gesture = 'NONE'

                if center and show_windows:
                    cv2.circle(frame, center, 5, (255, 180, 100), -1, cv2.LINE_AA)

        if frame_gesture == 'NONE':
            gesture_history.clear()
            stable_gesture = 'NONE'
        else:
            gesture_history.append(frame_gesture)
            stable_gesture = 'NONE'
            if gesture_history.count('OPEN') >= MIN_VOTES:
                stable_gesture = 'OPEN'
            elif gesture_history.count('FIST') >= MIN_VOTES:
                stable_gesture = 'FIST'

        now = time.perf_counter()
        display_gesture = stable_gesture if stable_gesture != 'NONE' else frame_gesture

        if stable_gesture == 'OPEN' and center is not None and prev_center is not None:
            dx = center[0] - prev_center[0]
            dy = center[1] - prev_center[1]
            if abs(dx) > abs(dy) and abs(dx) > 25 and now - last_action_time > COOLDOWN:
                if dx < 0:
                    pyautogui.hotkey('alt', 'shift', 'tab')
                    display_gesture = 'PREV WINDOW'
                else:
                    pyautogui.hotkey('alt', 'tab')
                    display_gesture = 'NEXT WINDOW'
                last_action_time = now

        prev_center = center

        if show_windows:
            try:
                draw_jarvis_grid(frame)
                ready = (now - last_action_time) >= COOLDOWN
                cooldown = max(0.0, COOLDOWN - (now - last_action_time))
                draw_hud_panel(frame, display_gesture, finger_count, ready, cooldown, now)
                draw_target_reticle(frame, bbox, center, now)
                draw_scanning_line(frame, bbox, now)
                draw_status_text(frame, bbox, 'TRACKING', now)

                cv2.putText(frame, 'PRESS Q TO QUIT', (18, frame.shape[0] - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (170, 210, 255), 1, cv2.LINE_AA)
                cv2.imshow('JARVIS Gesture Control', frame)
                cv2.imshow('Mask', mask)
            except cv2.error as exc:
                print(f'Camera display error: {exc}')
                show_windows = False

        if show_windows:
            try:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except cv2.error:
                break

        elapsed = time.perf_counter() - start
        if elapsed < 1 / TARGET_FPS:
            time.sleep(1 / TARGET_FPS - elapsed)
except KeyboardInterrupt:
    print('Stopped by user.')
except Exception as exc:
    print(f'Gesture loop stopped unexpectedly: {exc}')
finally:
    cap.release()
    if show_windows:
        cv2.destroyAllWindows()
