from kivymd.uix.boxlayout        import MDBoxLayout
from kivymd.uix.card             import MDCard
from kivymd.uix.navigationdrawer import MDNavigationDrawerDivider
from kivymd.material_resources   import dp

from kivy.properties import StringProperty
from lib.utils.label import CustomLabel


class GpsDisplay(MDCard):
    '''
        A custom card widget for displaying GPS information.

        The widget displays two pieces of text stacked vertically with a
        divider between them. It is styled as a Material Design card with
        slight elevation for emphasis.

        Attributes:
            text1 (StringProperty): Top label text (e.g., title or key).
            text2 (StringProperty): Bottom label text (e.g., value or detail).
            txt (str): Internal variable for tracking the bottom text.
    '''
    text1 = StringProperty(None)
    text2 = StringProperty(None)

    def __init__(self, **kwargs):
        '''
            Initialize the GPS display card and construct its layout.

            The layout consists of:
                - A top label (`text1`) aligned slightly to the right.
                - A divider for visual separation.
                - A bottom label (`text2`) centered horizontally.
        '''
        super().__init__(**kwargs)

        self.elevation = 2
        self.add_widget \
        (
            MDBoxLayout
            (
                CustomLabel
                (
                    text      = self.text1,
                    size_hint = [1, 0.3],
                    pos_hint  = {'center_x': 0.6}
                ),
                MDNavigationDrawerDivider(padding = [dp(10), dp(0), dp(10), dp(0)]),
                CustomLabel
                (
                    text   = self.text2,
                    halign = 'center'
                ),
                orientation = 'vertical'
            )

        )
        self.txt = self.children[0].children[0].text

    def txt_upd(self, txt):
        self.txt = txt

    def txt_show(self):
        return self.txt

