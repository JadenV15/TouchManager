from .ui import *

if __name__ == '__main__':
    res = Ask.option(
        title="Dinner",
        message="Choose your meal:",
        options=[
            (
                "Large Italian pizza",
                "code_name_pizza",
                "Mushrooms, cheese, truffle oil, tomato sauce, basil leaves"
            ),
            (
                "Bowl of pasta",
                "code_name_pasta",
                "Cheese, basil, tomato sauce"
            ),
        ],
        default="code_name_pasta"
    )
    
    print(res)
    
    res = Ask.button_option(
        title="Action",
        message="Save yourself or the whole world?",
        options=[
            ("Me", "yourself"),
            ("The World", "world")
        ],
        lock=False
    )
    
    print(res)