from app import create_app

try:
    app = create_app()
except Exception as e:
    import traceback
    print("!!!!! APP STARTUP ERROR !!!!!")
    traceback.print_exc()
    raise
