import re
import statistics
import random
import sys
import pandas as pd
from .utils import  chartdict,set_chart

# # import vega_template
# """
# convert all columns to string, in order to json_
# """
# def outputConvert(df):
#     columns = df.columns
#     for col in columns:
#         df[col] = df[col].astype(str)
#     return df

class AutoVega():
    def __init__(self, dataframe, chart=None,**kwargs):
        self.dataframe = dataframe 
        self.__data = dataframe
        # self.template = dict_template
        self.chart = set_chart(chart)
        self.__convert_dtypes()
        self.kwargs = kwargs
        self._uri_column = self._set_uri_column()
        self._date_column = self._set_date_column()
        self._numerical_column = self._set_numerical_column()
        self._coordinate_column = self._set_coordinate_column()
        self._img_column = self._set_image_column()
        self._label_column = self._set_label_column()
        self.__candidate_visualization = self.__find_candidate()
    def __plot_randomize(self, candidate_visualization):
      """
      Plot two of recommendation chart chart

      Returns:
          (list) candidate: List of recommendation chart name      
      """
      list_of_random_items = random.sample(candidate_visualization, 4)
      print(f"We show below two of them {tuple(list_of_random_items)} as illustrations: ")
      scripts = []
      for idx,name in enumerate(list_of_random_items):
        figure = chartdict[name.lower()](self.__data, self.kwargs)
        scripts.append(figure.plot())
        print(name, figure.plot()['encoding'])
      return scripts 

    def plot(self):
      """
      Plot visualization with suitable corresponding chart

      """
      chart_list = chartdict.keys()
      print(chart_list)
      figure = None
      if len(self.__data) != 0:
        print(self.chart)
        print(self.__candidate_visualization)
        if self.chart not in chart_list:
          if len(self.__candidate_visualization) > 1:
            print(f"You haven’t selected the chart type for your query result visualization.")
            print(f"Based on your query result data, we suggest to choose one of the following chart type: {self.__candidate_visualization}\n")
            return self.__plot_randomize(self.__candidate_visualization)
          else:
            figure = chartdict["table"](self.__data, self.kwargs)
            return [figure.plot()]
        else: ## pre-defined 
          if self.chart in self.__candidate_visualization:
            figure = chartdict[self.chart](self.__data, self.kwargs)
            return [figure.plot()]
          elif self.chart == 'map':
            if 'id' in self._numerical_column:
                print('ready to draw')
                figure = chartdict[self.chart](self.__data, self.kwargs)
                return [figure.plot()]
          else:
            print(f"Based on your query result data, we suggest to choose one of the following chart type: {self.__candidate_visualization}\n")
      else:
        print("No matching records found")
    # def show_candidate(self):
    #     print(self.__candidate_visualization)
    def __find_candidate(self):
      """
      Find candidate of visualization

      Returns:
          (list) candidate: List of recommendation chart name      
      """
      chart_list = list(chartdict.keys())
      candidate = []
      for idx,name in enumerate(chart_list):
          check = chartdict[name.lower()](self.__data, self.kwargs)
          if check.promote_to_candidate():
            candidate.append(name)
      return candidate
    def __convert_dtypes(self):
        """
        Convert data type each column of dataframe

        Parameters:
            (pandas.Dataframe) dataframe: The table

        Returns:
            (pandas.Dataframe) table: The result table             
        """

        for column in self.dataframe:
            try:
                self.dataframe[column] = self.dataframe[column].astype('string')
            except ValueError:
                pass

        for column in self.dataframe:
            try:
                self.dataframe[column] = self.dataframe[column].astype('datetime64')
            except ValueError:
                pass

        for column in self.dataframe:
            try:
                self.dataframe[column] = self.dataframe[column].astype('float64')
            except (ValueError, TypeError):
                pass

    def _set_numerical_column(self):
            """
            Get date column name of dataframe based on date data type
            """
            numerical_column = [name for name in self.dataframe.columns if self.dataframe[name].dtypes == 'float64']

            return numerical_column 
    def _set_uri_column(self):
            """
            Get date column name of dataframe based on date data type
            """
            #Regex pattern
            """
            Get uri column name of dataframe based on regex pattern

            :return: (list) uri_column: list of uri variable
            """
            #Regex pattern
            pattern_url = r"^(?:http(s)?:\/\/)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$(?<!.[jpg|gif|png|JPG|PNG])" 
            uri_column = self.set_column_based_on_regex(pattern_url)
            return uri_column
    def _set_image_column(self):
            """
            Get image column name of dataframe based on regex pattern

            :return: (list) image_column: list of image variable
            """
            #Regex pattern
            pattern_img = r"^http(s)?://(?:[a-z0-9\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|jpeg|gif|png|JPG|JPEG|Jpeg)$"        
            image_column = self.set_column_based_on_regex(pattern_img)

            return image_column
    def _set_coordinate_column(self):
            """
            Get coordinate column name of dataframe based on regex pattern

            :return: (list) coordinate_column: list of coordinate variable
            """
            #Regex pattern
            pattern_coordinate1 = r"^Point"
            pattern_coordinate2 = r"^POINT"
            coordinate_column1 = self.set_column_based_on_regex(pattern_coordinate1)
            coordinate_column2 = self.set_column_based_on_regex(pattern_coordinate2)

            coordinate_column = coordinate_column1 + coordinate_column2
            return coordinate_column

    def set_column_based_on_regex(self, pattern):
        """
        Set list of column name based on regex matching

        :return: (list) column: list of name
        """
        list_column = []

        for i in range (len(self.dataframe.columns)):
            column_name = self.dataframe.columns[i]
            column = self.dataframe[self.dataframe.columns[i]]
            is_matched_column = self.check_data_per_column(column, pattern)
            if is_matched_column:
                list_column.append(column_name)
#         print(list_column)
        return list_column

    def check_data_per_column(self, column, pattern):
        """
        Check entire data per column of dataframe if matched with regex pattern

        Parameters:
            (pandas.Dataframe) column: column of dataframe
            (string) pattern: regex pattern

        Returns:
            (boolen) boolean_check: The result table             
        """
        boolean_check = False
        for datapoint in range(len(column)):
            data = column.iloc[datapoint]
            try:
                if re.match(pattern, data):
                    boolean_check = True
            except TypeError:
                pass
                
        return boolean_check
    def _set_date_column(self):
        """
        Get date column name of dataframe based on date data type
        """
        date_column = [name for name in self.dataframe.columns if self.dataframe[name].dtypes == 'datetime64[ns]']

        return date_column
    def _set_label_column(self):
        """
        Get label column name of dataframe based on 'string' dtypes 
            with excluded uri, image url and coordinate column

        :return: (list) label_column: list of label column        
        """
        str_column = list(self.dataframe.columns)
#         print(self._uri_column, self._img_column, self._coordinate_column, self._numerical_column, self._date_column)
        #exclude uri, image url, coordinate column
        excluded_column = self._uri_column + self._img_column + self._coordinate_column + self._numerical_column + self._date_column
        label_column = [i for i in str_column + excluded_column if i not in str_column or i not in excluded_column]

        return label_column
    
# sys.modules[__name__] = AutoVega