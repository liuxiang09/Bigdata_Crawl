import pyfpgrowth
import pandas as pd
import matplotlib.pyplot as plt

# 构建样本数据
transactions = [['A', 'B', 'E'], ['B', 'D'], ['B', 'C'], ['A', 'B', 'D'], ['A', 'C'], ['B', 'C'], ['A', 'C'],
                ['A', 'B', 'C', 'E']]

# 读取文件，提取出第二列开始的所有交易品种
df = pd.read_csv('../交易品种/量化组.csv', sep='\t', header=None, encoding='gbk')
# 打印数据
# print(df)
# 根据逗号分割数据
df = df[0].str.split(',', expand=True)
# 打印数据
# print(df)

# 提取出df的第二列到最后一列
transactions = df.iloc[:, 1:].values.tolist()
# 去除空值和None
transactions = [[item for item in transaction if item is not None and item != ''] for transaction in transactions]
# 打印数据
#print(transactions)
# 输出transactions到文件
# with open('./交易品种/交易品种16.txt', 'w') as f:
#     for transaction in transactions:
#         f.write(','.join(transaction) + '\n')
# 使用 FP-Growth 算法找出频繁模式
patterns = pyfpgrowth.find_frequent_patterns(transactions, 50)  # 最小支持阈值为 2

rules = pyfpgrowth.generate_association_rules(patterns, 0.9)  # 置信度阈值为 0.7

sorted_rules = sorted(rules.items(), key=lambda x: x[1][1], reverse=True)

#print("关联规则：", sorted_rules)

# 打开文件以写入
with open('量化组.txt', 'w', encoding='utf-8') as file:
    for antecedent, (consequent, confidence) in sorted_rules:
        print(f"{antecedent} -> {consequent}, Confidence: {confidence}")
        file.write(f"{antecedent} -> {consequent}, Confidence: {confidence}\n")
# print("频繁模式：", patterns)
