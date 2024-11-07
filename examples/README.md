PONTS pour la V5


Création de plusieurs modèles :

* Modèle "HAUT"
Un modèle avec une sélection des points les plus hauts sur une grille (20cm) pour bien matérialiser les bords du tabliers de pont 
(bien sur sous les arbres ce sera pas idéal mais c'est surtout pour les cas où le tablier est bien dégagé). 
Cela leur permet d'être précis sur la largeur du pont


* Modèle "MNT"
Ce modèle issue d'une classification grossière du sol est complété par l'ajout d'une détection du tablier 
(la détection du sol étant une recherche des points bas et une triangulation de ceux-ci, on obtiendrait pas toujours le tablier sur les grands ponts 
où le lidar est passé en dessous, ou la ou le tablier est plus long que large) puis nous calculons le modèle au pas de 20cm. 
Ce type de représentation permet de générer du bruit quand il y a superposition de niveaux de sol et cela indique à l'opérateur ou est la culée du pont. 
Cela l'aide donc dans certain cas à déterminer la longueur du tablier cette fois.

