from kivy.properties import StringProperty, ObjectProperty, DictProperty

from kivymd.material_resources import dp
from kivymd.uix.boxlayout      import MDBoxLayout
from kivymd.uix.card           import MDCard
from kivymd.uix.list           import BaseListItem

from lib.utils.label import CustomLabel
from lib.utils.map   import Map


class ListItem(BaseListItem):
    '''
        A custom list item widget that displays a map thumbnail and a label inside a card.

        This widget is designed for use in lists of tracks or similar data, where each
        entry includes:
        - A small map preview (`Map`)
        - A text label (`CustomLabel`)
        - A press callback for interaction

        Attributes:
            txt (StringProperty): The main text to display in the label.
            item_press (ObjectProperty): Callback function to execute when the card is pressed.
            stats (DictProperty): Dictionary containing data for the item, such as
                ``points_to_show`` (a list of coordinates for the map thumbnail).
    '''
    txt        = StringProperty(None)
    item_press = ObjectProperty(None)
    stats      = DictProperty({})

    def __init__(self, **kwargs):
        '''
            Initialize the list item widget with a map thumbnail and label.
        '''
        super().__init__(**kwargs)

        self.divider = None
        self.height  = dp(80)

        self.add_widget \
        (
            MDCard
            (
            MDBoxLayout
                (
                    Map(points_to_show = self.stats['points_to_show']['value'], size_hint = [0.25, 1]),
                    MDBoxLayout
                    (
                        CustomLabel(text = self.txt, size_hint = [1, 0.5]),
                        orientation = 'vertical',
                        spacing     = dp(0),
                        padding     = [dp(10), dp(0), dp(5), dp(0)]
                    ),
                    spacing = dp(0),
                    padding = [dp(12), dp(0), dp(0), dp(0)]
                ),
                on_press  = self.item_press,
                pos_hint  = {'x': 0, 'y': 0.05},
                size_hint = [1, 0.95],
                elevation = 1,
                padding   = [dp(0), dp(0), dp(0), dp(0)]
            )

        )
