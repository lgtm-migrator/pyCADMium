"""
initialguessinvert.py
"""

import numpy as np
from scipy.sparse import spdiags, diags, csc_matrix
from scipy.sparse.linalg import spsolve 
from scipy.linalg import eig, eigh
from scipy.sparse.linalg import eigs

import sys


def initialguessinvert(self, ispin=0):

    v0 = np.zeros(( self.grid.Nelem, 1 ))
    n0 = np.zeros(( self.grid.Nelem, 1 ))

    if self.optPartition.ab_sym is not True:
        KSab = [self.KSa, self.KSb]
    else:
        KSab = [self.KSa]

    for i_KS in KSab:
        v0 += i_KS.veff[:, ispin][:, None] * i_KS.Q[:, ispin][:, None]

    if self.optPartition.ens_spin_sym is True:
        v0 = np.sum(v0, axis=1)
        for i_KS in KSab:
            ospin = 1 if ispin == 0 else 0
            v0 += (i_KS.veff[:, ospin] - max([i_KS.u])) * i_KS.Q[:, ospin]
        v0 = v0[:, None]

    if self.optPartition.ab_sym is True:
        v0 += self.grid.mirror(v0) 


    Wi = spdiags(data=2*np.pi*self.grid.hr*self.grid.ha*self.grid.wi, diags=0, m=self.grid.Nelem, n=self.grid.Nelem)
    W  = spdiags(self.grid.w, 0, self.grid.Nelem, self.grid.Nelem)

    Nsol = 0
    for i_KS in KSab:
        Nsol = max( Nsol, i_KS.solver[:, ispin].shape[0] )

    Ts = 0
    d    = np.empty((Nsol,1), dtype=object)
    phi0 = np.empty((Nsol,1), dtype=object)

    for i in range(1, Nsol+1):

        phi = None
        H0  = None
        m   = None

        #Alpha Kohn Sham object
        if len( self.KSa.solver[:,ispin]) >= i-1:
            phi = self.KSa.solver[i-1, ispin].phi 
            self.KSa.solver[i-1, ispin].hamiltonian()
            H0  = self.KSa.solver[i-1, ispin].H0
            m   = self.KSb.solver[i-1, ispin].m
        else:
            pass

        if self.optPartition.ab_sym is True:
            phi = np.hstack((phi, self.grid.mirror( self.KSa.solver[i-1, ispin].phi )))
        else:#Beta Kohn Sham object
            if len(self.KSb.solver) >= i-1:
                phi = self.KSb.solver[i-1,ispin].phi
                if H0 is None:
                    H0 = self.KSb.solver[i-1, ispin].H0
                if m is None:
                    m = self.KSb.solver[i-1, ispin].m
        
        S0 = np.diag(phi.T @ W @ Wi @ phi) ** 0.5
        phi = phi / S0
        S = phi.T @ W @ Wi @ phi
        H = spsolve(csc_matrix(W), H0) + csc_matrix(spdiags(v0[:,0], 0, self.grid.Nelem, self.grid.Nelem))
        F = phi.T @ (W @ Wi @ H @ phi)
        ev, v = eig(a=F, b=S)
        indx = np.argsort(ev)
        d = ev[indx].real
        v = v[:, indx]

        # print("Phi before multiplication by v\n", phi)

        phi = phi @ v

        # print("Phi before normaliation\n", phi)

        if self.optPartition.ens_spin_sym:
            if m == 0:
                phi0 = (phi / np.diag(phi.T @ W @ Wi @ phi)**0.5) * (1**0.5)
                Eks  = np.sum(d)
            else:
                phi0 = (phi / np.diag(phi.T @ W @ Wi @ phi)**0.5) * (2**0.5)
                Eks = 2 * np.sum(d)

        else:
            if m == 0:
                phi0 = (phi / np.diag(phi.T @ W @ Wi @ phi)**0.5) * (2**(0.5))
                Eks = 2 * np.sum(d)
            else: 
                phi0 = (phi / np.diag(phi.T @ W @ Wi @ phi)**0.5) * (4**(0.5))
                Eks = 4 * np.sum(d)

        Ts += Eks - self.grid.integrate( np.sum(phi0**2, axis=1) * np.squeeze(v0) )
        n0 += np.sum( phi0**2, axis=1 )[:, None]

    phi0 = phi0.flatten(order="F")[:, None]
    e0 = d.flatten()
    
    return phi0, e0, v0


        




