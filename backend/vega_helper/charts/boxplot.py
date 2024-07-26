from .chart import Chart
import plotly.express as px

class BoxPlot(Chart):
    def __init__(self, dataframe, kwargs):
        """
        Constructs all the necessary attributes for the BoxPlot object

        Parameters:
            dataframe (pandas.Dataframe): The dataframe
        """
        Chart.__init__(self, dataframe, kwargs)

    def promote_to_candidate(self):

        is_promote = self._is_var_exist(self._numerical_column, 1)

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
        Check the requirements for generating BoxPlot visualization

        Returns:
            (string) numerical_label: label of numerical column
            (list) group_column: categorical column
        """
        numerical_label = None
        group_column = None
        item_col, categorical_col = self._set_item_and_categorical()

        if self._is_var_exist(self._numerical_column, 1):
            numerical_label = self._numerical_column[0]
            if self._is_var_exist(categorical_col, 1):
                group_column= categorical_col
                
        return numerical_label, group_column      
    def genVega(self, data,  y, x=None, color=None):
        temp = {
            "data": {"values": data},
            "mark": {
                "type": "boxplot",
                "extent": "min-max"
            },
            "encoding": {
                "x": {"field": "", "type": "nominal"},
                "color": {"field": "", "type": "nominal", },
                "y": {
                    "field": y,
                    "type": "quantitative",
                }
            }
        }
        if y!=None:
            temp['encoding']['x']['field'] = x
        if color!=None:
            temp['encoding']['color']['field'] = color
        return temp
    
    def draw(self):
        """
        Generate BoxPlot visualization
        """
        numerical_label, group_column  = self._check_requirements()

        if numerical_label is not None and group_column is not None:
            if len(group_column) > 1:
                # fig = px.box(self.dataframe, x=group_column[1], y=numerical_label, color=group_column[0])
                # fig.show()
                return self.genVega(self.dataframe.filter(items=[ numerical_label, group_column[1], group_column[0]]).to_dict('records'), numerical_label,group_column[1],  group_column[0])
            else:
                # fig = px.box(self.dataframe, x=group_column[0], y=numerical_label)
                # fig.show()
                return self.genVega(self.dataframe.filter(items=[group_column[0], numerical_label]).to_dict('records'), numerical_label,group_column[0] )
        elif numerical_label is not None:
            # fig = px.box(self.dataframe, y=numerical_label)
            # fig.show()
            return self.genVega(self.dataframe.filter(items=[numerical_label]).to_dict('records'), numerical_label)
        else:
            pass                   