"""
    p4a hook that ONLY sets service attributes that buildozer.spec cannot express.
    - Targets your dist layout with no 'app/' module.
    - Patches both the dist-root manifest and the p4a template if present.
    - Works in both before_apk_build and after_apk_build across p4a versions.

    Notes:
    - Keep all <uses-permission> in buildozer.spec (android.permissions).
    - This hook does NOT add permissions.
"""

import os
from xml.etree import ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{%s}" % ANDROID_NS

# === CHANGE THIS if your service class name/package changes ===
TARGET_SERVICE = "org.prod.simplegpslogger.ServiceGpsservice"

# ---------------------- dist_dir discovery ----------------------

def _find_dist_dir_from_obj(obj):
    """
    Probe common p4a layouts for dist_dir on whatever is passed into the hook.
    Works when 'obj' is a Context, a ToolchainCL, or a wrapper.
    """
    if obj is None:
        return None

    # 1) Direct attribute (newer Contexts sometimes expose this)
    dist_dir = getattr(obj, "dist_dir", None)
    if dist_dir:
        return dist_dir

    # 2) Nested 'dist' (ctx.dist.dist_dir)
    dist = getattr(obj, "dist", None)
    if dist:
        dist_dir = getattr(dist, "dist_dir", None)
        if dist_dir:
            return dist_dir

    # 3) Internal Distribution on toolchain-like objects (toolchain._dist.dist_dir)
    _dist = getattr(obj, "_dist", None)
    if _dist:
        dist_dir = getattr(_dist, "dist_dir", None)
        if dist_dir:
            return dist_dir

    # 4) Some p4a versions keep a ctx inside; recurse once
    inner_ctx = getattr(obj, "ctx", None)
    if inner_ctx and inner_ctx is not obj:
        return _find_dist_dir_from_obj(inner_ctx)

    return None


def _resolve_dist_dir(primary, **kwargs):
    """
        Find a dist_dir from the primary hook arg and/or kwargs.
    """
    dist_dir = _find_dist_dir_from_obj(primary)
    if dist_dir:
        return dist_dir

    # try kwargs
    for key in ("ctx", "toolchain"):
        if key in kwargs:
            dist_dir = _find_dist_dir_from_obj(kwargs[key])
            if dist_dir:
                return dist_dir
    return None

# ---------------------- manifest path helpers ----------------------

def _dist_manifest_candidates(dist_dir):
    """
        Prefer your dist-root manifest; keep a fallback for src/main.
    """
    return [
        os.path.join(dist_dir, "AndroidManifest.xml"),
        os.path.join(dist_dir, "src", "main", "AndroidManifest.xml"),
    ]


def _template_candidate(dist_dir):
    return os.path.join(dist_dir, "templates", "AndroidManifest.tmpl.xml")

# ---------------------- XML patch (parsable manifests) ----------------------

def _ensure_service_attrs_xml(root):
    """
        Only set attributes on the target <service>.
        DO NOT add permissions here.
    """
    changed = False
    for svc in root.iter("service"):
        if svc.get(A + "name") == TARGET_SERVICE:
            if svc.get(A + "exported") != "false":
                svc.set(A + "exported", "false")
                changed = True
            if svc.get(A + "foregroundServiceType") != "location":
                svc.set(A + "foregroundServiceType", "location")
                changed = True
            return changed
    print(f"[HOOK] WARNING: Service '{TARGET_SERVICE}' not found in XML manifest.")
    return False


def _patch_manifest_xml(path):
    if not os.path.exists(path):
        return False, False
    try:
        ET.register_namespace("android", ANDROID_NS)
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        print(f"[HOOK] Could not parse XML ({path}); skipping. Err: {e}")
        return True, False

    changed = _ensure_service_attrs_xml(root)
    if changed:
        tree.write(path, encoding="utf-8", xml_declaration=True)
        print("[HOOK] Saved:", path)
    else:
        print("[HOOK] No attribute changes needed:", path)
    return True, changed

# -------- Template patch (string-safe: templates may include Jinja vars) -----

def _patch_template(path):
    """
        String-based patch for template files (avoid strict XML parse).
        Only injects/ensures service attributes for TARGET_SERVICE.
    """
    if not os.path.exists(path):
        return False, False

    try:
        txt = open(path, "r", encoding="utf-8").read()
    except Exception:
        txt = open(path, "r").read()

    changed = False
    if TARGET_SERVICE not in txt:
        print(f"[HOOK] WARNING: Service '{TARGET_SERVICE}' not found in template.")
    else:
        # Ensure android:exported
        if 'android:exported="false"' not in txt:
            new_txt = txt.replace(
                f'android:name="{TARGET_SERVICE}"',
                f'android:name="{TARGET_SERVICE}" android:exported="false"'
            )
            if new_txt != txt:
                txt = new_txt
                changed = True

        # Ensure android:foregroundServiceType
        if 'android:foregroundServiceType="location"' not in txt:
            new_txt = txt.replace(
                f'android:name="{TARGET_SERVICE}"',
                f'android:name="{TARGET_SERVICE}" android:foregroundServiceType="location"'
            )
            if new_txt != txt:
                txt = new_txt
                changed = True

    if changed:
        try:
            open(path, "w", encoding="utf-8").write(txt)
        except Exception:
            open(path, "w").write(txt)
        print("[HOOK] Saved template:", path)
    else:
        print("[HOOK] No attribute changes needed in template:", path)
    return True, changed

# ---------------------- Orchestrate patching ----------------------

def _patch_all(dist_dir):
    """
        Patch template first (so any later p4a render inherits attributes),
        then patch the concrete manifest(s) that exist in the dist.
    """
    found_any = False
    any_changed = False

    tmpl = _template_candidate(dist_dir)
    found, changed = _patch_template(tmpl)
    found_any |= found
    any_changed |= changed

    for path in _dist_manifest_candidates(dist_dir):
        if os.path.exists(path):
            print("[HOOK] Patching manifest:", path)
        found2, changed2 = _patch_manifest_xml(path)
        found_any |= found2
        any_changed |= changed2

    if not found_any:
        print("[HOOK] ERROR: No manifest/template candidates found under:", dist_dir)
        return False
    return any_changed

# ---------------------- Hook entry points ----------------------

def before_apk_build(ctx, **kwargs):
    """
        Run early to modify the template + current manifest in the dist.
        This ensures later build steps won't wipe your attributes.
    """
    dist_dir = _resolve_dist_dir(ctx, **kwargs)
    if not dist_dir:
        # Helpful diagnostics to adapt if p4a changes layouts in future
        try:
            print("[HOOK] DEBUG before_apk_build type(ctx):", type(ctx))
            print("[HOOK] DEBUG before_apk_build dir(ctx):", dir(ctx))
        except Exception:
            pass
        print("[HOOK] ERROR: Cannot locate dist_dir in before_apk_build(); skipping.")
        return False

    print("[HOOK] Using dist_dir (before):", dist_dir)
    return _patch_all(dist_dir)


def after_apk_build(toolchain, **kwargs):
    """
        Belt-and-suspenders: run again late to guard against any late file writes.
        Works across p4a versions by probing for _dist.dist_dir, ctx.dist, etc.
    """
    dist_dir = _resolve_dist_dir(toolchain, **kwargs)
    if not dist_dir:
        # Diagnostics
        try:
            print("[HOOK] DEBUG after_apk_build type(toolchain):", type(toolchain))
            print("[HOOK] DEBUG after_apk_build dir(toolchain):", dir(toolchain))
        except Exception:
            pass
        print("[HOOK] Cannot locate dist_dir in after_apk_build; skipping.")
        return False

    print("[HOOK] Using dist_dir (after):", dist_dir)
    return _patch_all(dist_dir)