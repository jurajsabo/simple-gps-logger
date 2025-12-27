from kivy.utils import platform


if platform == 'android':
    def extract_admob_id(file_path='secret.txt'):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ADMOB_BANNER_ID="):
                        return line.split("=", 1)[1]
        except Exception as e:
            print('[BANNER AD]', f'AdMob ID load failed: {e}')
            return None

    from jnius            import autoclass, cast
    from android.runnable import run_on_ui_thread
    from config           import ADMOB_BANNER_ID_default

    # ---------- Android plumbing ----------
    PythonActivity   = autoclass('org.kivy.android.PythonActivity')
    AdRequestBuilder = autoclass('com.google.android.gms.ads.AdRequest$Builder')
    AdSize           = autoclass('com.google.android.gms.ads.AdSize')
    AdView           = autoclass('com.google.android.gms.ads.AdView')
    MobileAds        = autoclass('com.google.android.gms.ads.MobileAds')

    DisplayMetrics = autoclass('android.util.DisplayMetrics')

    View                    = autoclass('android.view.View')
    ViewGroup               = autoclass('android.view.ViewGroup')
    Gravity                 = autoclass('android.view.Gravity')
    LayoutParams            = autoclass('android.view.ViewGroup$LayoutParams')
    FrameLayout             = autoclass('android.widget.FrameLayout')
    FrameLayoutLayoutParams = autoclass('android.widget.FrameLayout$LayoutParams')
    R_id                    = autoclass('android.R$id')

    ADMOB_BANNER_ID = extract_admob_id()
    BANNER_ID       = str(ADMOB_BANNER_ID) if ADMOB_BANNER_ID is not None else ADMOB_BANNER_ID_default

    class BannerAd:
        """
            Banner Ad wrapper for Kivy + AdMob (Android only).
            Uses Anchored Adaptive Banners.
        """

        TAG = 'KIVY_AD_BANNER_CONTAINER'

        def __init__(self):
            self.adview      = None
            self.container   = None
            self.initialized = False

            try:
                MobileAds.initialize(PythonActivity.mActivity, None)
                self.initialized = True
                print('[BANNER AD]', 'AdMob initialized')
            except Exception as e:
                print('[BANNER AD]', f'Failed to initialize AdMob: {e}')

        # ---------- internal helpers ----------
        def get_root(self):
            try:
                root = PythonActivity.mActivity.findViewById(R_id.content)
                return cast(ViewGroup, root)
            except Exception as e:
                print('[BANNER AD]', f'Could not get root content view: {e}')
                return None

        def remove_all_tagged_from_root(self) -> int:
            removed = 0
            try:
                root = self.get_root()
                if not root:
                    return 0

                while True:
                    v = root.findViewWithTag(self.TAG)
                    if not v:
                        break

                    parent = v.getParent()
                    if parent:
                        cast(ViewGroup, parent).removeView(v)
                    removed += 1

            except Exception as e:
                print('[BANNER AD]', f'Error removing tagged containers: {e}')

            return removed

        def get_adaptive_ad_size(self):
            """
                Returns an Anchored Adaptive Banner AdSize for the
                current orientation and screen width.
            """
            activity = PythonActivity.mActivity

            metrics = DisplayMetrics()
            activity.getWindowManager().getDefaultDisplay().getMetrics(metrics)

            width_px = metrics.widthPixels
            density  = metrics.density
            width_dp = int(width_px / density)

            return AdSize.getCurrentOrientationAnchoredAdaptiveBannerAdSize \
            (
                activity,
                width_dp
            )

        # ---------- public API ----------
        @run_on_ui_thread
        def create_and_load(self, unit_id: str = BANNER_ID, top: bool = True) -> bool:
            try:
                if self.adview or self.container:
                    self.destroy()

                removed = self.remove_all_tagged_from_root()
                if removed:
                    print('[BANNER AD]', f'Removed {removed} orphan container(s)')

                # --- Create AdView ---
                self.adview = AdView(PythonActivity.mActivity)
                self.adview.setAdUnitId(unit_id)
                self.adview.setAdSize(self.get_adaptive_ad_size())
                self.adview.setVisibility(View.GONE)

                # --- Container ---
                self.container = FrameLayout(PythonActivity.mActivity)
                self.container.setTag(self.TAG)

                params = FrameLayoutLayoutParams(
                    LayoutParams.MATCH_PARENT,
                    LayoutParams.WRAP_CONTENT
                )
                params.gravity = Gravity.TOP if top else Gravity.BOTTOM

                self.container.addView(self.adview)

                root = self.get_root()
                if not root:
                    print('[BANNER AD]', 'Root view not found')
                    return False

                root.addView(self.container, params)

                # --- Load ad ---
                request = AdRequestBuilder().build()
                self.adview.loadAd(request)

                print('[BANNER AD]', 'Adaptive banner created and loading')
                return True

            except Exception as e:
                print('[BANNER AD]', f'create_and_load failed: {e}')
                return False

        @run_on_ui_thread
        def show(self) -> bool:
            if not self.adview:
                return False

            try:
                self.adview.setVisibility(View.VISIBLE)
                return True
            except Exception as e:
                print('[BANNER AD]', f'Show failed: {e}')
                return False

        @run_on_ui_thread
        def destroy(self) -> bool:
            did_something = False

            try:
                if self.adview:
                    self.adview.destroy()
                    self.adview = None
                    did_something = True

                if self.container:
                    parent = self.container.getParent()
                    if parent:
                        cast(ViewGroup, parent).removeView(self.container)
                    self.container = None
                    did_something = True

                self.remove_all_tagged_from_root()
                return did_something

            except Exception as e:
                print('[BANNER AD]', f'Destroy failed: {e}')
                return False

        def ad_create(self, top = True):
            return self.create_and_load(top = top)

        def ad_show(self):
            return self.show()

else:
    class BannerAd:
        def __init__(self):
            print('[BANNER AD]', 'Android-only; no-op on this platform')

        def create_and_load(self):
            print('[BANNER AD]', 'create_and_load is Android-only')

        def show(self):
            print('[BANNER AD]', 'show is Android-only')

        def ad_create(self):
            print('[BANNER AD]', 'AD Create: Android-only. No-op on this platform.')
            return False

        def ad_show(self):
            print('[BANNER AD]', 'AD Show: Android-only. No-op on this platform.')
