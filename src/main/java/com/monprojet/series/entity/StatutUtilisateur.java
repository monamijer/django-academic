package com.monprojet.series.entity;

/**
 * Cycle de vie d'un compte utilisateur.
 * - EN_ATTENTE : créé par inscription, doit être approuvé par un admin
 * - APPROUVE   : peut se connecter et utiliser l'application
 * - REFUSE     : bloqué par un admin
 */
public enum StatutUtilisateur {
    EN_ATTENTE,
    APPROUVE,
    REFUSE
}