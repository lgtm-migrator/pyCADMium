"""
libxc.py
"""

from pylibxc import LibXCFunctional as Functional
import numpy as np

class Libxc():

    def __init__(self, grid, xc_family, func_id):

        self.grid = grid
        self.xc_family = xc_family
        self.func_id = func_id

    def get_xc_dictionary(self, n, pol):
        """
        Generates ingredients and computes e_xc and v_xc using Libxc
        """
        func_ingredients = {}
        func_ingredients["rho"] = n

        func = Functional(self.func_id, pol)

        if self.xc_family == 'lda':
            pass

        elif self.xc_family == 'gga':
            sigma = self.grid.sigma(n)
            func_ingredients["sigma"] = sigma

        else:
            raise ValueError("xc Functional family not recognized")

        xc_dictionary = func.compute(func_ingredients)
        return xc_dictionary

    def get_xc(self, n, return_epsilon=False):

        pol = n.shape[1]

        xc_dictionary = self.get_xc_dictionary(n, pol)
        epsilon = xc_dictionary["zk"]
        exc = self.grid.integrate(np.sum(epsilon.copy() * n, axis=1))

        #Calculate e_xc
        if self.xc_family == 'lda':
            vxc = xc_dictionary['vrho']        

        if self.xc_family == 'gga':
            vxc = xc_dictionary['vrho']
            vsigma = xc_dictionary['vsigma']

            if pol == 1:
                vxc = vxc - 2.0 * (self.grid.diva @ (vsigma * (self.grid.grada @ n))
                                  +self.grid.divr @ (vsigma * (self.grid.gradr @ n)))
            else:
                vxc[:, 0] = vxc[:,0] - 2.0 * (self.grid.diva @ (vsigma[:,0] * (self.grid.grada @ n[:,0])) 
                                             +self.grid.divr @ (vsigma[:,0] * (self.grid.gradr @ n[:,0]))) \
                                     - (self.grid.diva @ (vsigma[:,1] * (self.grid.grada @ n[:,1]))
                                       +self.grid.divr @ (vsigma[:,1] * (self.grid.gradr @ n[:,1])))

                vxc[:, 1] = vxc[:,1] - 2.0 * (self.grid.diva @ (vsigma[:,2] * (self.grid.grada @ n[:,1])) 
                                             +self.grid.divr @ (vsigma[:,2] * (self.grid.gradr @ n[:,1]))) \
                                     - (self.grid.diva @ (vsigma[:,1] * (self.grid.grada @ n[:,0]))
                                       +self.grid.divr @ (vsigma[:,1] * (self.grid.gradr @ n[:,0])))

        if return_epsilon is False:
            return exc, vxc
        
        else:
            return exc, epsilon, vxc