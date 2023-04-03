import pymysql
import pandas as pd
from pyecharts.charts import Pie
from pyecharts import options as opts
pymysql.install_as_MySQLdb()

conn = pymysql.connect(host='localhost', user='root', password='823223', port=3306, db='ttsx4')
df = pd.read_sql('SELECT * FROM df_order_info', con=conn)
x_name = ["准时", "不准时"]
# print(x_name)
i = 0
num = 0
num1 = 0
t = 0
x = df.sp3.count().item()
y = df["sp3"]

# for i in range(x):
#     # print(y[i])
#     t = int(y[i])
#     if t == 1:
#         num = num+1
#     else:
#         num1 = num1+1
# # print(df.sp3.count())
# print(num)
# print(num1)
# y_name = [num, num1]
# data = list(zip(x_name, y_name))
# a = (
#     Pie()
#         .add("", data_pair=data, radius='65%')
#         .set_global_opts(title_opts=opts.TitleOpts(title="准时率"), legend_opts=opts.LegendOpts(pos_left="80%"), )
#         .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
# )
# a.render()