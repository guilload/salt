# -*- coding: utf-8 -*-
'''
salting.py module of salt specific interfaces to raet

'''
# pylint: skip-file
# pylint: disable=W0611

# Import Python libs

# Import ioflo libs
from ioflo.base.odicting import odict

from ioflo.base.consoling import getConsole
console = getConsole()

from raet import raeting, nacling
from raet.road.keeping import RoadKeep

from salt.key import RaetKey

class SaltSafe(object):
    '''
    Interface between Salt Key management and RAET keep key management
    '''
    LocalFields = ['sighex', 'prihex', 'auto']
    RemoteFields = ['uid', 'name', 'acceptance', 'verhex', 'pubhex']

    def __init__(self, opts, **kwa):
        '''
        Setup SaltSafe instance
        '''
        self.auto = opts['auto_accept']
        self.dirpath = opts['pki_dir']
        self.saltRaetKey = RaetKey(opts)

    def verifyLocalData(self, data):
        '''
        Returns True if the fields in .LocalFields match the fields in data
        '''
        return (set(self.LocalFields) == set(data.keys()))

    def dumpLocalData(self, data):
        '''
        Dump the key data from the local estate
        '''
        self.saltRaetKey.write_local(data['prihex'], data['sighex'])

    def loadLocalData(self):
        '''
        Load and Return the data from the local estate
        '''
        data = self.saltRaetKey.read_local()
        if not data:
            return None
        return (odict(sighex=data['sign'], prihex=data['priv'], auto=self.auto))

    def clearLocalData(self):
        '''
        Load and Return the data from the local estate
        '''
        pass

    def verifyRemoteData(self, data):
        '''
        Returns True if the fields in .RemoteFields match the fields in data
        '''
        return (set(self.RemoteFields) == set(data.keys()))

    def dumpRemoteData(self, data, uid):
        '''
        Dump the data from the remote estate given by uid
        '''
        self.saltRaetKey.status(data['name'],
                                data['uid'],
                                data['pubhex'],
                                data['verhex'])

    def loadAllRemoteData(self):
        '''
        Load and Return the data from the all the remote estate files
        '''
        data = odict()

        for status, mids in self.saltRaetKey.list_keys().items():
            for mid in mids:
                keydata = self.saltRaetKey.read_remote(mid, status)
                if keydata:
                    rdata = odict()
                    rdata['uid'] = keydata['device_id']
                    rdata['name'] = keydata['minion_id']
                    rdata['acceptance'] = raeting.ACCEPTANCES[status]
                    rdata['verhex'] = keydata['verify']
                    rdata['pubhex'] = keydata['pub']
                    data[str(rdata['uid'])] = rdata

        return data

    def clearAllRemoteData(self):
        '''
        Remove all the remote estate files
        '''
        self.saltRaetKey.delete_all()

    def dumpLocal(self, local):
        '''
        Dump the key data from the local estate
        '''
        data = odict([
                        ('sighex', local.signer.keyhex),
                        ('prihex', local.priver.keyhex),
                        ('auto', self.auto),
                    ])
        if self.verifyLocalData(data):
            self.dumpLocalData(data)

    def dumpRemote(self, remote):
        '''
        Dump the data from the remote estate by calling status on it which
        will persist the data
        '''
        data = odict([
                        ('uid', remote.uid),
                        ('name', remote.name),
                        ('acceptance', remote.acceptance),
                        ('verhex', remote.verfer.keyhex),
                        ('pubhex', remote.pubber.keyhex),
                    ])
        if self.verifyRemoteData(data):
            self.dumpRemoteData(data, remote.uid)

    def loadRemote(self, remote):
        '''
        Load and Return the data from the remote estate file
        Override this in sub class to change uid
        '''
        #status = raeting.ACCEPTANCE_NAMES.get(remote.acceptance, 'accepted')
        #status='accepted'

        mid = remote.name
        statae = raeting.ACCEPTANCES.keys()
        for status in statae:
            keydata = self.saltRaetKey.read_remote(mid, status)
            if keydata:
                break
            
        if not keydata:
            return None

        data = odict()
        data['uid'] = keydata['device_id']
        data['name'] = keydata['minion_id']
        data['acceptance'] = raeting.ACCEPTANCES[status]
        data['verhex'] = keydata['verify']
        data['pubhex'] = keydata['pub']

        return data

    def clearRemote(self, remote):
        '''
        Salt level keys should not be auto removed with cache changes
        '''
        pass

    def replaceRemote(self, remote, old):
        '''
        Replace the safe keep key file at old name given remote.name has changed
        Assumes name uniqueness already taken care of
        '''
        new = remote.name
        if new != old:
            self.dumpRemote(remote) #will be pending by default unless autoaccept
            # manually fix up acceptance if not pending
            if remote.acceptance == raeting.acceptances.accepted:
                self.acceptRemote(remote)
            elif remote.acceptance == raeting.acceptances.rejected:
                self.rejectRemote(remote)
                
            self.saltRaetKey.delete_key(old) #now delete old key file

    def statusRemote(self, remote, verhex, pubhex, main=True):
        '''
        Evaluate acceptance status of remote estate per its keys
        persist key data differentially based on status
        '''
        status = raeting.ACCEPTANCES[self.saltRaetKey.status(remote.name,
                                                             remote.eid,
                                                             pubhex,
                                                             verhex)]

        if status != raeting.acceptances.rejected:
            if (verhex and verhex != remote.verfer.keyhex):
                remote.verfer = nacling.Verifier(verhex)
            if (pubhex and pubhex != remote.pubber.keyhex):
                remote.pubber = nacling.Publican(pubhex)
            remote.acceptance = status

        return status

    def rejectRemote(self, remote):
        '''
        Set acceptance status to rejected
        '''
        remote.acceptance = raeting.acceptances.rejected
        mid = remote.name
        self.saltRaetKey.reject(match=mid, include_accepted=True)

    def pendRemote(self, remote):
        '''
        Set acceptance status to pending
        '''
        pass

    def acceptRemote(self, remote):
        '''
        Set acceptance status to accepted
        '''
        remote.acceptance = raeting.acceptances.accepted
        mid = remote.name
        self.saltRaetKey.accept(match=mid, include_rejected=True)


def clearAllKeepSafe(dirpath, opts):
    '''
    Convenience function to clear all road and safe keep data in dirpath
    '''
    road = RoadKeep(dirpath=dirpath)
    road.clearLocalData()
    road.clearAllRemoteData()
    safe = SaltSafe(opts=opts)
    safe.clearLocalData()
    safe.clearAllRemoteData()
