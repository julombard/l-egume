from scipy import pi, array, sqrt

## gestion des enveloppe et des tropisme -> fonctions dans fichier R 'calc_root_tropism.r'

## recalcul de parametres

def update_root_params(ParamP):
    #liste des diametres de pointe racinaire par ordre
    lsDrac = [ParamP['Dmax']]
    intcpt= -ParamP['Dmin']*(ParamP['DIDm']-1) #calcul lucas -> bon
    for i in range(2): #?3/4? -> intiallemnt pour le moment nb_rac_ordre gere seulement jusqu'a ordre 2
        #Dfille = lsDrac[-1]*ParamP['DIDm'] #! bug a corriger : prendre en compte intercept lie a Dmin!
        Dfille = lsDrac[-1]*ParamP['DIDm']+intcpt # Version lucas: prends en compte intercept.

        if Dfille>=ParamP['Dmin']:
            lsDrac.append(Dfille)

    nb_ordre_rac = len(lsDrac)

    #liste de Vmax par ordre
    lsVrac = [ParamP['ELmax']]
    ELD = ParamP['ELmax'] / (ParamP['Dmax'] - ParamP['Dmin'])
    for i in range(1, nb_ordre_rac):
        #Vfille = lsVrac[-1] - ParamP['ELD']*(lsDrac[i-1]-lsDrac[i]) #bias dans les parametrage de 'ELD' (pas les pivots) -> a reprendre
        Vfille = lsVrac[-1] - ELD*(lsDrac[i-1]-lsDrac[i])

        lsVrac.append(Vfille)

    #liste des duree de croissance et root life span par ordre
    lsDur, lsSpan = [], []
    for i in range(nb_ordre_rac):
        lsDur.append(Dur_Growth_Root(lsDrac[i], ParamP['Dmax'], ParamP['GDs']))
        lsSpan.append(Life_Span_Root(lsDrac[i],ParamP['Dmax'],ParamP['FRD'],ParamP['LDs']))
        

    #liste demande potentiell apex par degre jour par ordre (pour atteindre Vmax)
    lsDemanDRac = [] 
    for i in range(nb_ordre_rac):
        increment_volDJ = lsVrac[i] * pi * (lsDrac[i]/2.)**2 #cm-3
        demande_masse = increment_volDJ * ParamP['FRD']
        lsDemanDRac.append(demande_masse)

    ParamP['lsDrac'] = lsDrac
    ParamP['nb_ordre_rac'] = nb_ordre_rac
    ParamP['lsVrac'] = lsVrac
    ParamP['lsDemanDRac'] = array(lsDemanDRac)
    ParamP['lsDurrac'] = lsDur
    ParamP['lsSpanrac'] = lsSpan
    ParamP['LDs2'] = lsSpan[1]#en degres jours 
    ParamP['LDs3'] = lsSpan[2]#en degres jours 
    ParamP['GDs1'] = ParamP['GDs']*(ParamP['Dmax']*10)**2#en degres jours 
    ParamP['GDs2'] = lsDur[1]#en degres jours 
    ParamP['GDs3'] = lsDur[2]#en degres jours 


    #recalcul d'anciens parametres utilises pour les enveloppes
    ParamP['Relongation_durationI'] = 1/lsVrac[0] #Thermal time for 1 cm of root - primary root (equivalent shoot phyllochron - degree.days.cm-1)
    ParamP['Relongation_durationII'] = 1/lsVrac[1] #Thermal time for 1 cm of root - secondary root (equivalent shoot phyllochron - degree.days.cm-1)
    ParamP['Relongation_duration0'] = ParamP['Relongation_durationI']*ParamP['LRS']#Thermal time to produce 1 root segment
    ParamP['delai_RLAP'] = ParamP['DistRA']*ParamP['Relongation_durationI']#delay before secondary root branching (degree.days)



## Gestion des racines fines

def nb_rac_ordre(ParamP, TT, satisfC=1., stressH=1.):
    """ liste de nombre de pointe racinaire par ordre issue d'un pivot au temps TT - 'satisfC' pour ajuster avec un facteur de stress C moyen sur TT
    - stressH, stress nhydrique moyen """
    ls_Nrac = [1]
    ordre = 1
    Lcum1 = max(0., ParamP['lsVrac'][ordre-1]*satisfC*TT - ParamP['DistRA'])
    Lcum1 = min(Lcum1, ParamP['lsDurrac'][ordre]*ParamP['lsVrac'][ordre-1]) #correction pour arret de developpement au bout d'un temps
    n = int( Lcum1/ ParamP['IBD'])
    ls_Nrac.append(n)

    if ParamP['nb_ordre_rac']>2:
        ordre = 2
        TTmoy2 = (ParamP['lsVrac'][ordre-2]*TT - ParamP['DistRA']) / (2*ParamP['lsVrac'][ordre-2]) #age moyen des secondaire
        Lcum2 = ParamP['lsVrac'][ordre-1]*satisfC*stressH*TTmoy2*n #longueur cumulee des secondaires
        Lcum_ram3 = max(0., Lcum2 - n*ParamP['DistRA']) #longueur reduite des distance apex non ramifiee sur lesquelles des tertiares sont presentes
        Lcum_ram3 = min(Lcum_ram3, n*ParamP['lsDurrac'][ordre]*ParamP['lsVrac'][ordre-1]) #correction pour arret de developpement au bout d'un temps
        n2 = int(Lcum_ram3 / ParamP['IBD']) #nb de tertiaire total
        ls_Nrac.append(n2)

    return array(ls_Nrac)
    #peut ajouter des duree max de developpement, voir senescence
    #peut ajouter un nb de nodales primaires
    #effet stressH pas ur primaire (RA() dans le model)?


#nb_rac_ordre(ParamP, 1000.)

def calc_DemandC_root(ParamP, ageTT, dTT, satisf=1.):
    """ demande d'un systeme pivotant """
    ls_Nrac = nb_rac_ordre(ParamP, ageTT, satisf)
    demande = sum(ParamP['lsDemanDRac'] * ls_Nrac) * dTT
    return demande, ls_Nrac
    # en C ou DM?


#AgePiv = {'0_0_5': 164.80000000000001, '0_0_4': 288.39999999999998, '0_0_0': 988.80000000000041, '0_1_4': 123.60000000000001, '0_1_5': 41.200000000000003, '0_1_2': 329.59999999999997, '0_1_3': 164.80000000000001, '0_3_2': 164.80000000000001, '0_3_3': 123.60000000000001, '0_3_0': 370.79999999999995, '0_3_1': 247.19999999999999, '0_3_4': 41.200000000000003}


def calc_DemandC_roots(ParamP, dAgePiv, dTT, dsatisfC):
    """ demande d'une serie de systeme pivotant d'age differents - dsatisf dico des staisf integree ds le temps"""
    demande = {}
    Nbrac = {}
    for k in dAgePiv.keys():
        nump = int(str.split(k, '_')[0])
        try:
            satisf_k = dsatisfC[k]
        except:#cle n'existe pas encore
            satisf_k = 1.

        demande[k], Nbrac[k] = calc_DemandC_root(ParamP[nump], dAgePiv[k], dTT[nump], satisf=satisf_k)

    return demande, Nbrac
    #calculer en meme temps somme des demandes plante?
    #sortir aussi les nb d'apex racinaires par ordre?


def calc_QDC_roots(dOffre,dDemand):
    """ calcul offre sur demande instantane """
    QD = {}
    for k in dOffre.keys():
        if dDemand[k]==0:
            ratio=1.
        else:
            ratio = dOffre[k] / dDemand[k]
            if ratio>1.:
                ratio=1.

        QD[k] = ratio

    return QD

def calc_QDCmoy_roots(dQD, dQDmoy, dAgePiv, dTT):
    """ calcul offre sur demande integre dans le temps """
    newQDmoy = {}
    for k in dQD.keys():
        nump = int(str.split(k, '_')[0])
        try:
            ratio = (dQDmoy[k]*dAgePiv[k] + dQD[k]*dTT[nump]) / (dAgePiv[k]+dTT[nump])
        except:
            ratio = dQD[k]

        newQDmoy[k] = ratio

    return newQDmoy
    #calculer QDmoy par plante?


def calc_StressHmoy_roots(dStressH, dPonder, dStressHmoy, dAgePiv, dTT):
    """ calcul offre sur demande integre dans le temps """
    newSressmoy = {}
    for k in dStressH.keys():
        nump = int(str.split(k, '_')[0])
        try:
            ratio = (dStressHmoy[k]*dAgePiv[k] + dStressH[k]/dPonder[k]*dTT[nump]) / (dAgePiv[k]+dTT[nump])
        except:
            ratio = dStressH[k]/dPonder[k]

        newSressmoy[k] = ratio

    return newSressmoy
    #calculer QDmoy par plante?


def get_QDCmoy(dQDC, idax):
    """ pour lire le ratio d'un axe - renvoie zero si cle pas existante"""
    try:
        ratio = dQDC[idax]
    except:
        ratio = 0.

    return ratio
    #commune au stress C et hydrique?



def dLong_root(ParamP, ls_Nrac, dTT, QD, StressH):
    """ increment de longueur par ordre pendant dTT """
    return ParamP['lsVrac']*ls_Nrac*dTT*QD*StressH


def calc_dLong_roots(ParamP, dNrac, dTT, dsatisfC, dStressH, dPonder):
    """ increment de longueur par ordre pendant dTT d'une serie de systeme pivotant d'age differents (cm) """
    ddl = {}
    for k in dNrac.keys():
        nump = int(str.split(k, '_')[0])
        try:
            satisf_k = dsatisfC[k]
        except:#cle n'existe pas encore
            satisf_k = 1.
        
        try:
            stressH =  dStressH[k] / dPonder[k]
        except:#cle n'existe pas encore
            stressH =  1.
        
        
        ddl[k] = dLong_root(ParamP[nump], dNrac[k], dTT[nump], satisf_k, stressH)#calc_DemandC_root(ParamP[nump], dAgePiv[k], dTT, satisf=satisf_k)

    return ddl

def cumul_plante_Lrac(nbplt, dCumlRac):
    """ renvoie cumul de longueur total par plante et par ordre (1,2,3) (en m) """
    cum1, cum2, cum3 = [],[],[]
    for i in range(nbplt): 
        cum1.append(0.)
        cum2.append(0.)
        cum3.append(0.)
    
    for k in dCumlRac.keys():
        nump = int(str.split(k, '_')[0])
        cum1[nump] += dCumlRac[k][0]/100.
        cum2[nump] += dCumlRac[k][1]/100.
        if len(dCumlRac[k])>2:
            cum3[nump] += dCumlRac[k][2]/100.

    tot = array(cum1)+ array(cum2)+ array(cum3)
    return cum1, cum2, cum3, tot.tolist()


def cumul_fine_Lrac(nbplt, dCumlRac):
    """ Lucas - renvoie cumul de longueur total excluant le pivot (aka longueur de racines fines) par plante (en m)"""
    cum1, cum2, cum3 = [],[],[]
    for i in range(nbplt): 
        cum1.append(0.)
        cum2.append(0.)
        cum3.append(0.)
    
    for k in dCumlRac.keys():
        nump = int(str.split(k, '_')[0])
        cum1[nump] += dCumlRac[k][0]/100.
        cum2[nump] += dCumlRac[k][1]/100.
        if len(dCumlRac[k])>2:
            cum3[nump] += dCumlRac[k][2]/100.

    tot = array(cum2)+ array(cum3)
    return tot.tolist()


def calc_QDplante(nbplt, dQD, dCumlRac, cumplantRac):
    """ calcul moyenne pondere par longueur des QD par plante"""
    res = []
    for i in range(nbplt): 
        res.append(0.)

    for k in dQD.keys():
        nump = int(str.split(k, '_')[0])
        res[nump] += dQD[k]*sum(dCumlRac[k])/(100.*cumplantRac[nump]+10e-15)

    return res

    

## Gestion des pivots
def calc_daxfPARaPiv(nbplantes, daxAgePiv, dpPARaF, daxPARaF):
    """ calcul de fraction de PARa par pivot selon PARa local de son axe porteur """
    #nbplantes = 1
    #dpPARaF = {'0':0.304275060431548}
    #daxPARaF = {'0_0_5': 0.0, '0_0_4': 0.0, '0_0_1': 0.0037106341514931427, '0_0_0': 0.031409083485574994, '0_0_3': 0.0, '0_0_2': 0.0, '0_1_4': 0.036519908098096465, '0_1_5': 0.046278225262069081, '0_1_6': 0.048053121501617661, '0_1_7': 0.00022389039194605387, '0_1_0': 0.027375781095510057, '0_1_1': 0.00050937561119222775, '0_1_2': 0.0, '0_1_3': 0.0, '0_3_2': 0.0, '0_3_3': 0.025585829814491427, '0_3_0': 0.001656678711150144, '0_3_1': 0.0, '0_3_6': 0.00017924845987041534, '0_3_4': 0.036519908098096465, '0_3_5': 0.046253375750383179}
    #lsAxPiv = ['0_0_0', '0_3_0', '0_3_1', '0_3_2', '0_3_3', '0_3_4', '0_1_2', '0_1_3', '0_1_4', '0_1_5', '0_0_4', '0_0_5']
    epsilon = 1e-12
    lsAxPiv = daxAgePiv.keys()
    
    reste_piv, nb_piv = [], []
    for i in range(nbplantes): reste_piv.append(0.);nb_piv.append(0)
    
    #quel PARa par plante sur des axes sans pivot?
    for k in daxPARaF:
        nump = int(str.split(k, '_')[0])
        if not k in lsAxPiv:
            reste_piv[nump] += daxPARaF[k]
        else:
            nb_piv[nump] += 1
    
    #PARa  par par pivot corrige en redistrbuant le PARa reste par plante sur des axes sans pivot (doit aussi marcher si un seul pivot!)
    daxPARaPiv = {}
    for k in lsAxPiv:
        nump = int(str.split(k, '_')[0])
        if nb_piv[nump]>1:#si plusieur pivot = proportionnel a proportion de rayonnement
            daxPARaPiv[k] = (daxPARaF[k] + reste_piv[nump] * daxPARaF[k]/(dpPARaF[str(nump)]-reste_piv[nump]+epsilon)) / (dpPARaF[str(nump)]+epsilon)
        else:#si un seul pivot (-> tout pour ce pivot)
            daxPARaPiv[k] = 1.#daxPARaF[k] + reste_piv[nump]
    
    return daxPARaPiv
    #fait bugger qd dpPARaF[str(nump)] = reste_piv[nump] -> ajoute un epsilon
    #fait bugger: dpPARaF = 0

def ponder_daxfPARaPiv_ax(daxPARaPiv, Frac_piv_sem, Frac_piv_loc):#ponder=[0.7, 0.2, 0.1]):
    """ ponderation des fraction daxPARaPiv sur un meme axe et avec racine seminale"""
    #ponder=[frac_locale, frac_reste_axe, frac_seminal]
    # ! ces fractions peuvent changer selon les geno/especes! -> changer ponder par plante
    epsilon = 1e-12
    lsAxPiv = daxPARaPiv.keys()
    daxPARaPiv_ponder = {}
    for k in lsAxPiv:#initialise a zero
        daxPARaPiv_ponder[k] = 0.
     
    #lsAxPiv = ['0_0_0', '0_3_0', '0_3_1', '0_3_2', '0_3_3', '0_3_4', '0_1_2', '0_1_3', '0_1_4', '0_1_5', '0_0_4', '0_0_5']
    for k in lsAxPiv:
        #etablit liste des apparentes (meme plante, meme axe)
        nump, nax, ram = int(str.split(k, '_')[0]), int(str.split(k, '_')[1]), int(str.split(k, '_')[2])
        ponder = [Frac_piv_loc[nump], 1.- Frac_piv_loc[nump] - Frac_piv_sem[nump], Frac_piv_sem[nump]] #ponder=[frac_locale, frac_reste_axe, frac_seminal]
        #print nump, ponder
        #ponder=[0.1, 0.2, 0.7]
        lsparent = []
        for ax in lsAxPiv:
            if int(str.split(ax, '_')[0])==nump and int(str.split(ax, '_')[1])==nax:
                lsparent.append(ax)

        #si seminale, pas de repartition
        if nax==0 and ram==0:
            daxPARaPiv_ponder[k] += daxPARaPiv[k]
        elif len(lsparent)==1:#pas seminale et pas de parent
            idseminal = str(nump)+'_0_0'
            daxPARaPiv_ponder[k] += daxPARaPiv[k]*(ponder[0]+ponder[1])
            daxPARaPiv_ponder[idseminal] += daxPARaPiv[k]*(ponder[2])
        else: #pas seminale et des parents sur l'axe
            idseminal = str(nump)+'_0_0'
            daxPARaPiv_ponder[k] += daxPARaPiv[k]*(ponder[0])
            daxPARaPiv_ponder[idseminal] += daxPARaPiv[k]*(ponder[2])
            nb_parent = float(len(lsparent)-1)
            for ax in lsparent:
                daxPARaPiv_ponder[ax] += daxPARaPiv[k]*(ponder[1]/nb_parent)

    return daxPARaPiv_ponder



def distrib_dM_ax(daxfPARaPiv, pivots, Frac_piv_sem, Frac_piv_loc):#ponder=[0.7, 0.2, 0.1]):
    """ distribue increment de biomasse (e.g de pivots/racfine) par plante a l'echelle axe en fonction des fractions daxfPARaPiv"""
    #ponderation de l'allocation locale
    daxPARaPiv_ponder = ponder_daxfPARaPiv_ax(daxfPARaPiv, Frac_piv_sem, Frac_piv_loc)#ponder)

    daxPiv = {}
    for k in daxfPARaPiv.keys():
        nump = int(str.split(k, '_')[0])
        dpiv = pivots[nump]
        #daxPiv[k] = daxfPARaPiv[k]*dpiv
        daxPiv[k] = daxPARaPiv_ponder[k]*dpiv
    
    return daxPiv#dictionnaire pivots echelle axe 

def calc_DiamPiv(ParamP, MaxPiv):
    """ calcule les diametres MAx de pivots a partir de dico axe des biomasses cumulee """
    DiampivMax = {}
    for k in MaxPiv.keys():
        nump = int(str.split(k, '_')[0])
        DPivot2_coeff = ParamP[nump]['DPivot2_coeff']
        DiampivMax[k] = sqrt(DPivot2_coeff * MaxPiv[k])
    return DiampivMax #dictionnaire des diametres par axe


def Dur_Growth_Root(D, Dmax, GDs):
    """ d'apres pages et al 2014 - Growth duration for root in function of their diameter (degree.days.mm2-1)"""
    # D (cm)
    # GDs (degree.days)
    if D==Dmax:
        GD = 10**9 
    else:
        GD = GDs*(D*10)**2

    return GD

#Dur_Growth_Root(D=0.1, Dmax=0.2, GDs=100*20)



def Life_Span_Root(D,Dmax,RTD,LDs):
    """ d'apres pages et al 2014 - Root Life span before decay in function of their diameter (degree day.mm.mg-1)"""
    # D (cm)
    # LDs (degree.days)
    # RTD (g.cm-3)
    if D==Dmax:
        LD = 10**9 
    else:
        LD = LDs * RTD * (D*10)**2

    return LD

#Life_Span_Root(D=0.1,Dmax=0.2,RTD=0.1,LDs=3000*20)



def calc_root_senescence(dl2, dl3, dur2, dur3, SRL):
    """ calcule de la senescende """
    #invar['dRLen2'], -> liste 'memoire' des dlroot par plante
    #invar['dRLen3'], -> liste 'memoire' des dlroot par plante
    #dur2, dur3, -> growth duration + life span(GDs+LDs) en jour a 20degre
    #invar['SRL'] -> current SRL

    dRLenSen2 = 0.*array(SRL)#initialise a zero
    dRLenSen3 = 0.*array(SRL)
    for nump in range(len(dur2)):
        if len(dl3)>(int(dur3[nump])+1):
            dLroot3 = dl3[-int(dur3[nump])][nump]
            if len(dl2)>(int(dur2[nump])+1):
                dLroot2 = dl2[-int(dur2[nump])][nump]
            else:
                dLroot2 = 0.
        else:
            dLroot2 = 0.
            dLroot3 = 0.
        
        dRLenSen2[nump] = dLroot2
        dRLenSen3[nump] = dLroot3
    
    
    dRLenSentot = dRLenSen2+dRLenSen3
    dMSenRoot = dRLenSentot/(SRL+10e-15)
    return dRLenSentot, dMSenRoot
