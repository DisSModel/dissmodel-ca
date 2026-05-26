from dissmodel.core import Environment
env = Environment(end_time=10)
print(dir(env))
print(f"Now: {env.now()}")
env.run() # This runs to the end
print(f"Now after run: {env.now()}")
