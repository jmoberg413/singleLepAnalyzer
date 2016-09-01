#!/usr/bin/python

import os,sys,time,math,datetime
parent = os.path.dirname(os.getcwd())
sys.path.append(parent)
from numpy import linspace
from weights import *
from analyzeAll import *
from samples import *
from ROOT import gROOT,TTree,TFile,TH1D
import pickle

def round_sig(x,sig=2):
	try:
		return round(x, sig-int(math.floor(math.log10(abs(x))))-1)
	except:
		return round(x,5)

gROOT.SetBatch(1)
start_time = time.time()

"""
Note: 
--Each process in step1 (or step2) directories should have the root files hadded! 
--The code will look for <step1Dir>/<process>_hadd.root for nominal trees.
The uncertainty shape shifted files will be taken from <step1Dir>/../<shape>/<process>_hadd.root,
where <shape> is for example "JECUp". hadder.py can be used to prepare input files this way! 
--Each process given in the lists below must have a definition in "samples.py"
--Check the set of cuts in "analyze.py"
"""

# INPUT
lumiStr = str(targetlumi/1000).replace('.','p') # 1/fb
step1Dir = '/user_data/jhogan/LJMet_1lepTT_082916_step2newSF/nominal/' #w/ new pdf weights

# OUTPUT
cTime=datetime.datetime.now()
datestr='%i_%i_%i'%(cTime.year,cTime.month,cTime.day)
timestr='%i_%i_%i'%(cTime.hour,cTime.minute,cTime.second)
pfix='kinematics'

##################################################
#################### CUTS ########################
##################################################

# region determines how jet/bjet/dR cuts work: PS, SR, CR (categorized), TTCR, WJCR (to give default btag cuts)
region = 'PS'
cutList = {'lepPtCut':40,
	   'leadJetPtCut':150, #300, #
	   'subLeadJetPtCut':75, #150, #
	   'thirdJetPtCut':30, #100, #
	   'metCut':60, #75, #
	   'njetsCut':3,
	   'nbjetsCut':0,
	   'drCut':0, #1.0, #
	   }

if len(sys.argv)>3: catList=[str(sys.argv[3])]
else: catList=['E','M','All']

# Systematics?
scaleSignalXsecTo1pb = False
doAllSys= True
doQ2sys = True
doJetRwt = True
isotrig = 1

cutString = 'lep'+str(int(cutList['lepPtCut']))+'_MET'+str(int(cutList['metCut']))+'_leadJet'+str(int(cutList['leadJetPtCut']))+'_subLeadJet'+str(int(cutList['subLeadJetPtCut']))+'_thirdJet'+str(int(cutList['thirdJetPtCut']))+'_NJets'+str(int(cutList['njetsCut']))+'_NBJets'+str(int(cutList['nbjetsCut']))+'_DR'+str(int(cutList['drCut']))


###########################################################
#################### HISTOGRAM DEFS #######################
###########################################################

#bigbins = [0,50,100,150,200,250,300,350,400,450,500,600,700,800,1000,1200,1500]
bigbins = [0,50,100,125,150,175,200,225,250,275,300,325,350,375,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2500,3000,3500,4000,5000]

plotList = {#discriminantName:(discriminantLJMETName, binning, xAxisLabel)

	'deltaRAK8':('minDR_leadAK8otherAK8',linspace(0,5,51).tolist(),';min #DeltaR(1^{st} AK8 jet, other AK8 jet)'),
	'MTlmet':('MT_lepMet',linspace(0,250,51).tolist(),';M_{T}(l,#slash{E}_{T}) [GeV]'),
	'NPV'   :('nPV_singleLepCalc',linspace(0, 30, 31).tolist(),';PV multiplicity;'),
	'lepPt' :('leptonPt_singleLepCalc',linspace(0, 1000, 51).tolist(),';Lepton p_{T} [GeV];'),
	'lepEta':('leptonEta_singleLepCalc',linspace(-4, 4, 41).tolist(),';Lepton #eta;'),
	'JetEta':('theJetEta_JetSubCalc_PtOrdered',linspace(-4, 4, 41).tolist(),';AK4 Jet #eta;'),
	'JetPt' :('theJetPt_JetSubCalc_PtOrdered',linspace(0, 1500, 51).tolist(),';jet p_{T} [GeV];'),
	'Jet1Pt':('theJetPt_JetSubCalc_PtOrdered[0]',linspace(0, 1500, 51).tolist(),';1^{st} AK4 Jet p_{T} [GeV];'),
	'Jet2Pt':('theJetPt_JetSubCalc_PtOrdered[1]',linspace(0, 1500, 51).tolist(),';2^{nd} AK4 Jet p_{T} [GeV];'),
	'Jet2Pt':('theJetPt_JetSubCalc_PtOrdered[1]',linspace(0, 1500, 51).tolist(),';2^{nd} AK4 Jet p_{T} [GeV];'),
	'Jet3Pt':('theJetPt_JetSubCalc_PtOrdered[2]',linspace(0, 800, 51).tolist(),';3^{rd} AK4 Jet p_{T} [GeV];'),
	'Jet4Pt':('theJetPt_JetSubCalc_PtOrdered[3]',linspace(0, 500, 51).tolist(),';4^{th} AK4 Jet p_{T} [GeV];'),
	'Jet5Pt':('theJetPt_JetSubCalc_PtOrdered[4]',linspace(0, 500, 51).tolist(),';5^{th} AK4 Jet p_{T} [GeV];'),
	'Jet6Pt':('theJetPt_JetSubCalc_PtOrdered[5]',linspace(0, 500, 51).tolist(),';6^{th} AK4 Jet p_{T} [GeV];'),
	'JetPtBins' :('theJetPt_JetSubCalc_PtOrdered',linspace(0,2000,21).tolist(),';AK4 Jet p_{T} [GeV];'),
	'Jet1PtBins':('theJetPt_JetSubCalc_PtOrdered[0]',linspace(0,2000,21).tolist(),';1^{st} AK4 Jet p_{T} [GeV];'),
	'Jet2PtBins':('theJetPt_JetSubCalc_PtOrdered[1]',linspace(0,2000,21).tolist(),';2^{nd} AK4 Jet p_{T} [GeV];'),
	'Jet3PtBins':('theJetPt_JetSubCalc_PtOrdered[2]',linspace(0,2000,21).tolist(),';3^{rd} AK4 Jet p_{T} [GeV];'),
	'Jet4PtBins':('theJetPt_JetSubCalc_PtOrdered[3]',linspace(0,2000,21).tolist(),';4^{th} AK4 Jet p_{T} [GeV];'),
	'Jet5PtBins':('theJetPt_JetSubCalc_PtOrdered[4]',linspace(0,2000,21).tolist(),';5^{th} AK4 Jet p_{T} [GeV];'),
	'Jet6PtBins':('theJetPt_JetSubCalc_PtOrdered[5]',linspace(0,2000,21).tolist(),';6^{th} AK4 Jet p_{T} [GeV];'),
	'HT'    :('AK4HT',linspace(0, 5000, 51).tolist(),';H_{T} [GeV];'),
	'ST'    :('AK4HTpMETpLepPt',linspace(0, 5000, 51).tolist(),';S_{T} [GeV];'),
	'MET'   :('corr_met_singleLepCalc',linspace(0, 1500, 51).tolist(),';#slash{E}_{T} [GeV];'),
	'NJets' :('NJets_JetSubCalc',linspace(0, 15, 16).tolist(),';jet multiplicity;'),
	'NBJets':('NJetsCSVwithSF_JetSubCalc',linspace(0, 10, 11).tolist(),';b tag multiplicity;'),
	'NWJets':('NJetsWtagged',linspace(0, 6, 7).tolist(),';W tag multiplicity;'),
	'NWJetsSmeared':('NJetsWtagged_0p6',linspace(0, 6, 7).tolist(),';W tag multiplicity;'),
	'NJetsAK8':('NJetsAK8_JetSubCalc',linspace(0, 8, 9).tolist(),';AK8 Jet multiplicity;'),
	'JetPtAK8':('theJetAK8Pt_JetSubCalc_PtOrdered',linspace(0, 1500, 51).tolist(),';AK8 Jet p_{T} [GeV];'),
	'JetPtBinsAK8':('theJetAK8Pt_JetSubCalc_PtOrdered',bigbins,';AK8 Jet p_{T} [GeV];'),
	'JetEtaAK8':('theJetAK8Eta_JetSubCalc_PtOrdered',linspace(-4, 4, 41).tolist(),';AK8 Jet #eta;'),
	'Tau21'  :('theJetAK8NjettinessTau2_JetSubCalc_PtOrdered/theJetAK8NjettinessTau1_JetSubCalc_PtOrdered',linspace(0, 1, 51).tolist(),';AK8 Jet #tau_{2}/#tau_{1};'),
	'Tau21Nm1'  :('theJetAK8NjettinessTau2_JetSubCalc_PtOrdered/theJetAK8NjettinessTau1_JetSubCalc_PtOrdered',linspace(0, 1, 51).tolist(),';AK8 Jet #tau_{2}/#tau_{1};'),
	'Pruned' :('theJetAK8PrunedMass_JetSubCalc_PtOrdered',linspace(0, 500, 51).tolist(),';AK8 Jet Pruned mass [GeV];'),
	'PrunedSmeared' :('theJetAK8PrunedMassJMRSmeared_JetSubCalc',linspace(0, 500, 51).tolist(),';AK8 Jet Pruned mass [GeV];'),
	'PrunedSmearedNm1' :('theJetAK8PrunedMassJMRSmeared_JetSubCalc',linspace(0, 500, 51).tolist(),';AK8 Jet Pruned mass [GeV];'),
	'mindeltaR':('deltaR_lepClosestJet',linspace(0, 5, 51).tolist(),';min #DeltaR(l, jet);'),
	'deltaRjet1':('deltaR_lepJets[0]',linspace(0, 5, 51).tolist(),';#DeltaR(l, 1^{st} jet);'),
	'deltaRjet2':('deltaR_lepJets[1]',linspace(0, 5, 51).tolist(),';#DeltaR(l, 2^{nd} jet);'),
	'deltaRjet3':('deltaR_lepJets[2]',linspace(0, 5, 51).tolist(),';#DeltaR(l, 3^{rd} jet);'),
	'minMlb' :('minMleppBjet',linspace(0, 1000, 51).tolist(),';min[M(l,b)] [GeV], #geq 1 b tags;'),  ## B TAG
	'nLepGen':('NLeptonDecays_TpTpCalc',linspace(0,10,11).tolist(),';N lepton decays from TT'),
	'METphi':('corr_met_phi_singleLepCalc',linspace(-3.2,3.2,65).tolist(),';#phi(#slash{E}_{T})'),
	'lepPhi':('leptonPhi_singleLepCalc',linspace(-3.2,3.2,65).tolist(),';#phi(l)'),
	'lepDxy':('leptonDxy_singleLepCalc',linspace(-0.02,0.02,51).tolist(),';lepton xy impact param [cm]'),
	'lepDz':('leptonDz_singleLepCalc',linspace(-0.1,0.1,51).tolist(),';lepton z impact param [cm]'),
	'lepCharge':('leptonCharge_singleLepCalc',linspace(-2,2,5).tolist(),';lepton charge'),
	'lepIso':('leptonMiniIso_singleLepCalc',linspace(0,0.2,51).tolist(),';lepton mini isolation'),
	'Tau1':('theJetAK8NjettinessTau1_JetSubCalc_PtOrdered',linspace(0,1,51).tolist(),';AK8 Jet #tau_{1}'),
	'Tau2':('theJetAK8NjettinessTau2_JetSubCalc_PtOrdered',linspace(0,1,51).tolist(),';AK8 Jet #tau_{2}'),
	'JetPhi':('theJetPhi_JetSubCalc_PtOrdered',linspace(-3.2,3.2,65).tolist(),';AK4 Jet #phi'),
	'JetPhiAK8':('theJetAK8Phi_JetSubCalc_PtOrdered',linspace(-3.2,3.2,65).tolist(),';AK8 Jet #phi'),
	'Bjet1Pt':('BJetLeadPtWithSF_JetSubCalc',linspace(0,1500,51).tolist(),';1^{st} b jet p_{T} [GeV]'),  ## B TAG
	'Wjet1Pt':('WJetLeadPt',linspace(0,1500,51).tolist(),';1^{st} W jet p_{T} [GeV]'),
	'topMass':('topMass',linspace(0,1500,51).tolist(),';reconstructed M(t) [GeV]'),
	'topPt':('topPt',linspace(0,1500,51).tolist(),';reconstructed pT(t) [GeV]'),
	'minMlj':('minMleppJet',linspace(0,1000,51).tolist(),';min[M(l,jet)] [GeV], 0 b tags'),
	'minMljDR':('deltaRlepJetInMinMljet',linspace(0,5,51).tolist(),';#DeltaR(l,jet) from min[M(l,jet)], 0 b tags'),
	'minMljDPhi':('deltaPhilepJetInMinMljet',linspace(0,5,51).tolist(),';#Delta#phi(l,jet) from min[M(l,jet)], 0 b tags'),
	'minMlbDR':('deltaRlepbJetInMinMlb',linspace(0,5,51).tolist(),';#DeltaR(l,b) from min[M(l,b)], > 1 b tags'), ## B TAG
	'minMlbDPhi':('deltaPhilepbJetInMinMlb',linspace(0,5,51).tolist(),';#Delta#phi(l,b) from min[M(l,b)], > 1 b tags'), ## B TAG
	'nonMinMlbDR':('deltaRlepbJetNotInMinMlb',linspace(0,5,51).tolist(),';#DeltaR(l,b) not in min[M(l,b)], > 1 b tags'),  ## B TAG
	'MWb1':('M_taggedW_bjet1',linspace(0,1000,51).tolist(),';M(W jet, 1^{st} b jet) [GeV]'), ## B TAG
	'MWb2':('M_taggedW_bjet2',linspace(0,1000,51).tolist(),';M(W jet, 2^{nd} b jet) [GeV]'), ## 2 B TAG
	'deltaRlb1':('deltaRlepbJet1',linspace(0,5,51).tolist(),';#DeltaR(l, 1^{st} b jet)'), ## B TAG
	'deltaRlb2':('deltaRlepbJet2',linspace(0,5,51).tolist(),';#DeltaR(l, 2^{nd} b jet)'), ## 2 B TAG
	'deltaRtW':('deltaRtopWjet',linspace(0,5,51).tolist(),';#DeltaR(reco t, W jet)'),
	'deltaRlW':('deltaRlepWjet',linspace(0,5,51).tolist(),';#DeltaR(l, W jet)'),
	'deltaRWb1':('deltaRtaggedWbJet1',linspace(0,5,51).tolist(),';#DeltaR(W, 1^{st} b jet)'), ## B TAG
	'deltaRWb2':('deltaRtaggedWbJet2',linspace(0,5,51).tolist(),';#DeltaR(W, 2^{nd} b jet)'), ## 2 B TAG
	'deltaPhilb1':('deltaPhilepbJet1',linspace(0,5,51).tolist(),';#Delta#phi(l, 1^{st} b jet)'), ## B TAG
	'deltaPhilb2':('deltaPhilepbJet2',linspace(0,5,51).tolist(),';#Delta#phi(l, 2^{nd} b jet)'), ## 2 B TAG
	'deltaPhitW':('deltaPhitopWjet',linspace(0,5,51).tolist(),';#Delta#phi(reco t, W jet)'),
	'deltaPhilW':('deltaPhilepWjet',linspace(0,5,51).tolist(),';#Delta#phi(l, W jet)'),
	'deltaPhiWb1':('deltaPhitaggedWbJet1',linspace(0,5,51).tolist(),';#Delta#phi(W, 1^{st} b jet)'), ## B TAG
	'deltaPhiWb2':('deltaPhitaggedWbJet2',linspace(0,5,51).tolist(),';#Delta#phi(W, 2^{nd} b jet)'), ## 2 B TAG
	'WjetPt':('WJetTaggedPt',linspace(0,1500,51).tolist(),';W jet p_{T} [GeV]'),
	'PtRel':('PtRelLepClosestJet',linspace(0,500,51).tolist(),';p_{T,rel}(l, closest jet) [GeV]'),
	}

###########################################################
#################### SAMPLE GROUPS ########################
###########################################################

bkgList = [
	#'WJetsMG',
	#'TTJetsMG',
	#'TTJetsPH700to1000inc',
	#'TTJetsPH700mtt',
	#'QCDht100','QCDht200',
	'DY50',
	'WJetsMG100',
	'WJetsMG200',
	'WJetsMG400',
	'WJetsMG600',
	'WJetsMG800',
	'WJetsMG1200',
	'WJetsMG2500',
	'WW','WZ','ZZ',
	'TTJetsPH0to1000inc',
	'TTJetsPH1000toINFinc',
	'TTJetsPH1000mtt',
	'TTWl','TTWq',
	'TTZl','TTZq',
	'Tt','Tbt','Ts',
	'TtW','TbtW',
	'QCDht300','QCDht500','QCDht700','QCDht1000','QCDht1500','QCDht2000',
	]

whichSignal = 'TT' #TT, BB, or T53T53
signalMassRange = [700,1800]
sigList = [whichSignal+'M'+str(mass) for mass in range(signalMassRange[0],signalMassRange[1]+100,100)]
if whichSignal=='T53T53': sigList = [whichSignal+'M'+str(mass)+chiral for mass in range(signalMassRange[0],signalMassRange[1]+100,100) for chiral in ['left','right']]
if whichSignal=='TT': decays = ['BWBW','THTH','TZTZ','TZBW','THBW','TZTH'] #T' decays
if whichSignal=='BB': decays = ['TWTW','BHBH','BZBZ','BZTW','BHTW','BZBH'] #B' decays
if whichSignal=='T53T53': decays = [''] #decays to tWtW 100% of the time

dataList = ['DataERRC','DataERRD','DataEPRD','DataMRRC','DataMRRD','DataMPRD']

q2List  = [#energy scale sample to be processed
	'TTJetsPHQ2U','TTJetsPHQ2D',
	#'TtWQ2U','TbtWQ2U',
	#'TtWQ2D','TbtWQ2D',
	]

###########################################################
#################### NORMALIZATIONS #######################
###########################################################

def negBinCorrection(hist): #set negative bin contents to zero and adjust the normalization
	norm0=hist.Integral()
	for iBin in range(0,hist.GetNbinsX()+2):
		if hist.GetBinContent(iBin)<0: hist.SetBinContent(iBin,0)
		if hist.Integral()!=0 and norm0>0: hist.Scale(norm0/hist.Integral())
		
def overflow(hist):
	nBinsX=hist.GetXaxis().GetNbins()
	content=hist.GetBinContent(nBinsX)+hist.GetBinContent(nBinsX+1)
	error=math.sqrt(hist.GetBinError(nBinsX)**2+hist.GetBinError(nBinsX+1)**2)
	hist.SetBinContent(nBinsX,content)
	hist.SetBinError(nBinsX,error)
	hist.SetBinContent(nBinsX+1,0)
	hist.SetBinError(nBinsX+1,0)

###########################################################
################### READ INPUT FILES ######################
###########################################################

def readTree(file):
	if not os.path.exists(file): 
		print "Error: File does not exist! Aborting ...",file
		os._exit(1)
	tFile = TFile(file,'READ')
	tTree = tFile.Get('ljmet')
	return tFile, tTree 

print "READING TREES"
shapesFiles = ['jec','jer','btag']
tTreeData = {}
tFileData = {}
for data in dataList:
	print "READING:", data
	tFileData[data],tTreeData[data]=readTree(step1Dir+'/'+samples[data]+'_hadd.root')

tTreeSig = {}
tFileSig = {}
for sig in signals:
	for decay in decays:
		print "READING:", sig+decay
		print "        nominal"
		tFileSig[sig+decay],tTreeSig[sig+decay]=readTree(step1Dir+'/'+samples[sig+decay]+'_hadd.root')
		if doAllSys:
			for syst in shapesFiles:
				for ud in ['Up','Down']:
					print "        "+syst+ud
					tFileSig[sig+decay+syst+ud],tTreeSig[sig+decay+syst+ud]=readTree(step1Dir.replace('nominal',syst.upper()+ud.lower())+'/'+samples[sig+decay]+'_hadd.root')

tTreeBkg = {}
tFileBkg = {}
for bkg in bkgList+q2List:
	print "READING:",bkg
	print "        nominal"
	tFileBkg[bkg],tTreeBkg[bkg]=readTree(step1Dir+'/'+samples[bkg]+'_hadd.root')
	if doAllSys:
		for syst in shapesFiles:
			for ud in ['Up','Down']:
				if bkg in q2List:
					tFileBkg[bkg+syst+ud],tTreeBkg[bkg+syst+ud]=None,None
				else:
					print "        "+syst+ud
					tFileBkg[bkg+syst+ud],tTreeBkg[bkg+syst+ud]=readTree(step1Dir.replace('nominal',syst.upper()+ud.lower())+'/'+samples[bkg]+'_hadd.root')

print "FINISHED READING"

###########################################################
#################### RUN ANALYSE.PY #######################
###########################################################

#def analyze(tTree,process,cutList,isotrig,doAllSys,doJetRwt,discriminantName,discriminantDetails,category,region):

if len(sys.argv)>2: iPlot=sys.argv[2]
else: iPlot='minMlb'
print "PLOTTING:",iPlot
print "         LJMET Variable:",plotList[iPlot][0]
print "         X-AXIS TITLE  :",plotList[iPlot][2]
print "         BINNING USED  :",plotList[iPlot][1]

nCats  = len(catList)
catInd = 1
for category in catList:
	print category
	datahists = {}
	bkghists  = {}
	sighists  = {}
	if len(sys.argv)>1: outDir=sys.argv[1]
	else: 
		outDir = os.getcwd()+'/'+pfix
		if not os.path.exists(outDir+'/'+category): os.system('mkdir -p '+outDir+'/'+category)
		outDir+='/'+category
	for data in dataList: 
		datahists.update(analyze(tTreeData,data,cutList,isotrig,False,doJetRwt,iPlot,plotList[iPlot],category,region))
		if catInd==nCats: del tFileData[data]
	for bkg in bkgList: 
		bkghists.update(analyze(tTreeBkg,bkg,cutList,isotrig,doAllSys,doJetRwt,iPlot,plotList[iPlot],category,region))
		if catInd==nCats: del tFileBkg[bkg]
		if doAllSys and catInd==nCats:
			for syst in shapesFiles:
				for ud in ['Up','Down']: del tFileBkg[bkg+syst+ud]
	for sig in sigList: 
		for decay in decays: 
			sighists.update(analyze(tTreeSig,sig+decay,cutList,isotrig,doAllSys,doJetRwt,iPlot,plotList[iPlot],category,region))
			if catInd==nCats: del tFileSig[sig+decay]
			if doAllSys and catInd==nCats:
				for syst in shapesFiles:
					for ud in ['Up','Down']: del tFileSig[sig+decay+syst+ud]
	if doQ2sys: 
		for q2 in q2List: 
			bkghists.update(analyze(tTreeBkg,q2,cutList,isotrig,False,doJetRwt,iPlot,plotList[iPlot],category,region))
			if catInd==nCats: del tFileBkg[q2]

	#Negative Bin Correction
	for bkg in bkghists.keys(): negBinCorrection(bkghists[bkg])

	#OverFlow Correction
	for data in datahists.keys(): overflow(datahists[data])
	for bkg in bkghists.keys():   overflow(bkghists[bkg])
	for sig in sighists.keys():   overflow(sighists[sig])

	pickle.dump(datahists,open(outDir+'/datahists_'+iPlot+'.p','wb'))
	pickle.dump(bkghists,open(outDir+'/bkghists_'+iPlot+'.p','wb'))
	pickle.dump(sighists,open(outDir+'/sighists_'+iPlot+'.p','wb'))
	catInd+=1


print("--- %s minutes ---" % (round((time.time() - start_time)/60,2)))

