"""
Filter tools menu

Functions for printing and eliminating spikes in the currently selected trajectories.

Printing is done to the terminal window.  Spikes are found using a hardcoded acceleration value that
is similar to the default value in the Trajectory Window (150m/s^2).  It is not currently possible to
query the value in the Trajectory editor.

The median cut filter is a special filter that finds the median value of the curve around the location
of the spike then replaces the 'spike' with that median value.  One characteristic of this filter is
that applying it twice (or more) has no effect on the data.  This filter in conjunction with a smoothing
filter makes for a great way of eliminating spikes in trajectories.
"""
import sys
import os
import inspect
import importlib
import math

this_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
if this_dir not in sys.path:
    sys.path.append(this_dir)

import qtm

import helpers.menu_tools
import helpers.traj

from helpers.vector import Vec3

importlib.reload(helpers.menu_tools)
importlib.reload(helpers.traj)

from helpers.menu_tools import add_menu_item, add_command

from collections import Counter


# - - - - - - - - - - - - - - - - - -
# ////////   P R I V A T E  ////////
# - - - - - - - - - - - - - - - -

CLOSEST_SAMPLES = 30


def _fix_trajectory(traj):
    cur_frame = qtm.gui.timeline.get_current_frame()
    cur_sample = qtm.data.series._3d.get_sample(traj['id'], cur_frame)
    cur_pos = Vec3(cur_sample['position'])
    try:
        samples = {
            s['id']: [
                Vec3(x['position']) 
                for x in qtm.data.series._3d.get_samples(s['id'])
                if x is not None
            ]
            for s in trouble_trajectories
        }    
    except TypeError as te:
        qtm.gui.message.add_message(str(te), str(trouble_trajectories), 'error')

    distances = [
        (id, (s - cur_pos).magnitude())
        for id, samples in samples.items()
        for s in samples
    ]
    sort_distances = sorted(distances, key=lambda x: x[1])
    closest = [x[0] for x in sort_distances[:CLOSEST_SAMPLES]]
    count = Counter(closest)
    try:
        new_id = count.most_common(1)[0][0]
        qtm.data.object.trajectory.move_parts(traj['id'], new_id)
        qtm.gui.message.add_message('Labeled as: ' + qtm.data.object.trajectory.get_label(new_id), '', 'info')
    except Exception as e:
        qtm.gui.message.add_message(str(e), str(count.most_common(1)), 'error')


# - - - - - - - - - - - - - - - - - -
# ////////   P U B L I C   ////////
# - - - - - - - - - - - - - - - -

trouble_trajectories = []

def load_trouble_trajectories():
    global trouble_trajectories
    trouble_trajectories = [
        s for s in qtm.gui.selection.get_selections()
        if qtm.data.object.trajectory.get_label(s['id']) is not None
    ]
    message = ('Selected trajectories:\n' + 
               '\n'.join([qtm.data.object.trajectory.get_label(s['id']) for s in trouble_trajectories]))
    qtm.gui.message.add_message(message, '', 'info')


def fix_trouble_trajectory():
    selections = qtm.gui.selection.get_selections()
    if len(trouble_trajectories) == 0:
        qtm.gui.message.add_message('No trouble trajectories loaded.', '', 'error')
    elif len(selections) > 1:
        qtm.gui.message.add_message('Multiple trajectories selected.', '', 'error')
    elif len(selections) == 0:
        qtm.gui.message.add_message('No trajectories selected.', '', 'error')
    else:
        _fix_trajectory(selections[0])


def unload_trouble_trajectories():
    trouble_trajectories = []
    pass

# region [ COLLAPSE / EXPAND ]
menu_priority = 10
def add_menu():

    add_command("load_trouble_trajectories", load_trouble_trajectories)
    add_command("fix_trouble_trajectory", fix_trouble_trajectory)
    add_command("unload_trouble_trajectories", unload_trouble_trajectories)

    menu_id = qtm.gui.insert_menu_submenu(None,"Fix")
    add_menu_item(menu_id, "Load trouble trajectories", "load_trouble_trajectories")
    add_menu_item(menu_id, "Unload trouble trajectories", "load_trouble_trajectories")
    add_menu_item(menu_id, "Fix selected trajectory", "fix_trouble_trajectory")
    #qtm.gui.set_accelerator( {"ctrl": True, "alt": False, "shift": True, "key": "f"}, "fix_trouble_trajectory")
    qtm.gui.set_accelerator( {"ctrl": True, "alt": False, "shift": True, "key": "x"}, "fix_trouble_trajectory")

# endregion

if __name__ == "__main__":
    add_menu()