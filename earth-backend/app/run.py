import uvicorn


def main():
    uvicorn.run("main:app", reload=True)

if __name__ == "__main__":
    main()
