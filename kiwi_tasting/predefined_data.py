#  OpenKiwi: Open-Source Machine Translation Quality Estimation
#  Copyright (C) 2020 Unbabel <openkiwi@unbabel.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

source_sentences = [
    "to add or remove pixels when resizing so the image retains approximately the same appearance at a different size , select Resample Image .",
    "to update all assignments in the current document , choose Update All Assignments from the Assignments panel menu .",
    "in the Options tab , click the Custom button and enter lower values for Error Correction Level and Y / X Ratio .",
    "for example , you could create a document containing a car that moves across the Stage .",
    "in the New From Template dialog box , locate and select a template , and click New .",
    "make sure that you obtained the security settings file from a source that you trust .",
    "makes a rectangular selection ( or a square , when used with the Shift key ) .",
    "drag diagonally from the corner where you want the graph to begin to the opposite corner .",
    "enter a value from -100 % to 100 % to specify the percentage by which to decrease or increase the color or the spot-color tint .",
    "you can enable the Contribute publishing server using this dialog box .",
]

target_sentences = [
    'wählen Sie " Bild neu berechnen , " um beim Ändern der Bildgröße Pixel hinzuzufügen oder zu entfernen , damit das Bild ungefähr dieselbe Größe aufweist wie die andere Größe .',
    'wenn Sie alle Aufgaben im aktuellen Dokument aktualisieren möchten , wählen Sie im Menü des Aufgabenbedienfelds die Option " Alle Aufgaben aktualisieren . "',
    'klicken Sie auf der Registerkarte " Optionen " auf die Schaltfläche " Benutzerdefiniert " und geben Sie Werte für " Fehlerkorrektur-Level " und " Y / X-Verhältnis " ein .',
    "Sie können beispielsweise ein Dokument erstellen , das ein Auto über die Bühne enthält .",
    'wählen Sie im Dialogfeld " Neu aus Vorlage " eine Vorlage aus und klicken Sie auf " Neu . "',
    "stellen Sie sicher , dass Sie die Datei für die Sicherheitseinstellungen von einer vertrauenswürdigen Quelle stammen .",
    "erstellt eine rechteckige Auswahl ( oder ein Quadrat , wenn sie mit der Umschalttaste verwendet wird ) .",
    "ziehen Sie den Zeiger an die Stelle , an der das Diagramm mit der anderen Ecke beginnen soll .",
    "geben Sie einen Wert zwischen -100 % und 100 % ein , um den Prozentwert festzulegen , um den die Farbe oder der Volltonfarbton zu verringern oder zu erhöhen .",
    "Sie können den Contribute-Veröffentlichungsserver über dieses Dialogfeld aktivieren .",
]

word_tags = [
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK OK OK OK OK OK BAD OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK BAD OK OK OK OK OK BAD OK BAD OK OK OK BAD OK OK OK OK OK OK OK BAD OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK BAD OK OK OK OK OK BAD OK BAD OK BAD OK OK OK BAD OK OK OK OK OK OK OK",
    "OK OK OK OK BAD BAD OK BAD OK BAD OK BAD OK BAD OK OK OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK BAD OK OK OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK BAD OK BAD OK OK OK OK BAD BAD OK OK OK",
    "OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK",
]

sentence_hter = [
    0.322581,
    0.000000,
    0.064516,
    0.263158,
    0.000000,
    0.312500,
    0.375000,
    0.727273,
    0.161290,
    0.000000,
]
