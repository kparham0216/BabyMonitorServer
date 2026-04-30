import matplotlib.pyplot as plt
import csv

rows = []
with open("output.csv", "r") as file:
    reader = csv.reader(file)
    
    for row in reader:
        rows.append(row)
    
temp_read = [float(i) for i in rows[0]]
temp_act = [float(i) for i in rows[1]]

time_steps = list(range(1, len(temp_read) + 1))

plt.plot(time_steps, temp_read, color='r', label='Observed', marker='o', linestyle='-')
plt.plot(time_steps, temp_act, color='g', label='Control', marker='o', linestyle='-')
plt.ylim(80, 90)
plt.yticks(range(80, 91))
plt.title('Temp Accuracy - 3 Minutes')
plt.xlabel('Time Index')
plt.ylabel('Temp (°F)')
plt.xticks(time_steps)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()
