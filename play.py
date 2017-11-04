from attenuator import *

#ww = WriteConflict()
#ww.grow_n(5)
#ww.graph("ww")

cd = CircularDependency()
cd.grow_n(25)
#cd.graph("cd")


#for i in range(0, 10):
#    ad = AntiDependency()
#    ad.grow_n(2)
#    ad.graph("ad" + str(i))

#ad = AntiDependency()
#ad.grow(15)
#ad.graph("ad")

cd.graph("Cd")
hg = HyperDSG(cd)

dot = hg.to_dot()
dot.render("FOO")


#hg2 = HyperDSG(ad)
#dot = hg2.to_dot#()
#dot.render("BAR")

#ad.shrink()

#ad.graph("ad2")

