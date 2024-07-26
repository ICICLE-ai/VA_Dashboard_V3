from .chart import Chart
import plotly.express as px

class DonutChart(Chart):
    def __init__(self, dataframe, kwargs):
        """
        Constructs all the necessary attributes for the DonutChart object

        Parameters:
            dataframe (pandas.Dataframe): The dataframe
        """
        Chart.__init__(self, dataframe, kwargs)

    def promote_to_candidate(self):

        is_promote = self._is_var_exist(self._label_column, 1) and self._is_var_exist(self._numerical_column, 1)

        return is_promote

    def plot(self):
        """
        Generate visualization
        """
        if self.promote_to_candidate():
            return self.draw()
        else:
            pass

    def _check_requirements(self):
        """
        Check the requirements for generating DonutChart visualization

        Returns:
            (string) label_name: label name
            (list) numerical_var: numerical var
        """
        label_name = None
        numerical_var = None
        
        if self._is_var_exist(self._numerical_column, 1):
            numerical_var = self._numerical_column[0]
            if self._is_var_exist(self._label_column, 1):
                label_name = self._label_column[0]

        
        return label_name, numerical_var    
    def genVega(self, data, theta, color):
        temp = {
            "data": {"values": data},
            "mark": {"type": "arc", "innerRadius": 50},
            "encoding": {
                "theta": {"field": theta, "type": "quantitative"},
                "color": {"field": color, "type": "nominal"}
            }
        }
        return temp 
    def draw(self):
        """
        Generate PieChart visualization
        """
        label_name, numerical_var  = self._check_requirements()

        if label_name is not None and numerical_var is not None:
            # fig = px.pie(self.dataframe, values=numerical_var, names=label_name, hole=0.3)
            # fig.show()                
            return self.genVega(self.dataframe.filter(items=[numerical_var, label_name]).to_dict('records'), numerical_var, label_name)