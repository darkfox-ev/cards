from crib import crib

if __name__ == '__main__':
    p1 = crib.Player()
    p2 = crib.AI_Player()
    g = crib.Game(2, [p1, p2])
    g.play()
