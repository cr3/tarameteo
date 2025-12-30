Import("env")
env.Append(LINKFLAGS=["--coverage"])
env.Append(LIBS=["gcov"])
