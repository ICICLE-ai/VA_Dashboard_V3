from .chart import Chart
import folium
from IPython.display import display

class Map(Chart):
    def __init__(self, dataframe, kwargs):
        """
        Constructs all the necessary attributes for the Map object

        Parameters:
            dataframe (pandas.Dataframe): The dataframe
        """
        Chart.__init__(self, dataframe, kwargs)

    def promote_to_candidate(self):

        is_promote = self._is_var_exist(self._coordinate_column, 1)

        return is_promote
    
    def _check_requirements(self):
        """
        Check the requirements for generating tree visualization

        Returns:
            (list) popup_data: list of label name
        """
        # popup_data = None
        # if self._is_var_exist(self._coordinate_column, 1):
        #     new_data = self._add_point()
        #     if len(self._label_column) == 0:
        #         popup_data = new_data.coordinate_point
        #     else:
        #         popup_data = new_data[self._label_column[0]]
        # else:
        #     popup_data = None
        
        # return popup_data
        if self._is_var_exist(self._numerical_column, 1) and 'id' in self._label_column:
            return self._numerical_column


    def plot(self):
        """
        Generate Image Grid visualization
        """
        return self.draw()
        # if self._is_var_exist(self._coordinate_column, 1):
        #     self.draw()
        # else:
        #     pass

               

    def _add_point(self):
        """
        Add coordinate column for coordinate folium map

        Returns:
            (pandas.Dataframe): Dataframe with new coordinate column
        """
        copy_data = self.dataframe.copy()

        coor_var = self._coordinate_column[0]    
        #Get coordinate data (latitude and longitude)
        char_delete = 'Point()OINT'
        copy_data['coordinate_point'] = copy_data[coor_var]
        dataframe_new = copy_data.coordinate_point.astype(str).apply(lambda S:S.strip(char_delete))
        dataframe_new = dataframe_new.to_frame()
        new = dataframe_new[dataframe_new.columns[-1]].str.split(" ", n = 1, expand = True)
        new = new.astype('float64')
        copy_data['coordinate'] = new.apply(lambda x: list([x[1], x[0]]),axis=1)

        return copy_data
    def genVega(self, data):

        temp = {
            'data': {'values':data},
            "transform": [
                {
                "lookup": "id",
                "from": {
                    "data": {
                    "url": "https://raw.githubusercontent.com/vega/vega/main/docs/data/us-10m.json",
                    "format": {
                        "type": "topojson",
                        "feature": "states"
                    }
                    },
                    "key": "id"
                },
                "as": "geo"
                }
            ],
            "projection": {"type": "albersUsa"},
            "mark": "geoshape",
            'encoding': {
                'shape': {'field': 'geo','type': 'geojson'},
                'color': {'field': 'value', 'type': 'quantitative'},
                'row': {'field': 'group'}
            }
        }
        print(temp)
        return temp 

    def truncate_data(self, data):

        if len(data) > 2000 :
            truncate_data = data.head(2000)
            data = truncate_data
            print(f"Time limit exceed... Showing only 2000 coordinates")
        else:
            pass

        return data
    
    
    def draw(self):
        """
        Generate map visualization
        """
        return self.genVega(self.dataframe.to_dict('records'))


