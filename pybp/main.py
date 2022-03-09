import projgen


def main():
    plan = projgen.PyProject()
    plan.setup_prompts()
    plan.execute()


if __name__ == "__main__":
    main()
