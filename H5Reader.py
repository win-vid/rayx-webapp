import h5py


class H5Reader:

    """
    H5Reader is obsolete now because RayX is called with the python package and does not need to output a .h5 file anymore

    The H5Reader classes is designed to read RayX.h5 files and return the data as a dictionary
    """

    path_to_h5 = None

    def __init__(self, path_to_h5):
        self.path_to_h5 = path_to_h5
        pass

    def get_event_data(self, event_key):

        """
        Returns a list of event data for a given event key

        RayX - Event Keys in H5-File:
        'direction_x', 'direction_y', 'direction_z', 'electric_field_x', 'electric_field_y', 'electric_field_z', 
        'energy', 'event_type', 'object_id', 'optical_path_length', 'order', 'path_event_id', 'path_id', 'position_x', 
        'position_y', 'position_z', 'rand_counter', 'source_id'
        """

        with h5py.File(self.path_to_h5, 'r') as h5_file:
            
            # data["rayx"]["events"][event_key][i]
            events_data = h5_file["rayx"]["events"]         

            if event_key in events_data:
                return list(events_data[event_key])

            return None

    def get_all_events_data(self):

        """
        Returns a dictionary of all event data. Each key is a dataset name.
        """

        with h5py.File(self.path_to_h5, "r") as f:
            events_group = f["rayx"]["events"] 

            # list dataset names inside the group
            field_names = list(events_group.keys())

            # read each dataset into a numpy array
            data = {name: events_group[name][:] for name in field_names}

            n = len(data[field_names[0]])

            # build a list of rows: each row is a dict mapping field->value
            rows = []
            for i in range(n):
                row = {name: data[name][i] for name in field_names}
                rows.append(row)

        return rows

    def set_path_to_h5(self, path_to_h5):

        """
        Sets the path to the h5 file
        """

        self.path_to_h5 = path_to_h5