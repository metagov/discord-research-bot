from discord.ui import View

def construct_view(_id, items):
    view = View(timeout=None)
    for Item in items:
        view.add_item(Item(_id))
    
    return view