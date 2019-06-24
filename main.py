from simulator.game import Game

if __name__ == "__main__":
    game = Game()
    game.new()
    for i in range(5):
        print("\n"+str(game.tick()))
        input("Press enter to age a year")
