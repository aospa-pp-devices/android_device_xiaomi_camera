#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import os
import shutil
import zipfile

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = []

def lib_fixup_campostproc_system_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_system' if partition == 'system' else None

lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'vendor.xiaomi.hardware.campostproc@1.0',
    ): lib_fixup_campostproc_system_suffix,
}

def save_pristine_apk_impl(ctx, file, file_path, *args, **kwargs):
    # Keep a copy of the pristine apk: the apktool round-trip recompiles
    # resources.arsc, which breaks the obfu_res name mapping the camera uses
    # for its drawables at runtime.
    shutil.copyfile(file_path, f'{file_path}.pristine')


def restore_pristine_resources_impl(ctx, file, file_path, *args, **kwargs):
    # Swap back the original resources.arsc/res/assets: only the manifest and
    # the smali are interesting from the apktool round-trip.
    pristine = zipfile.ZipFile(f'{file_path}.pristine')
    patched = zipfile.ZipFile(file_path)
    keep = {'AndroidManifest.xml'} | {
        n for n in patched.namelist() if n.startswith('classes') and n.endswith('.dex')
    }
    out = zipfile.ZipFile(f'{file_path}.new', 'w')
    for info in pristine.infolist():
        data = patched.read(info.filename) if info.filename in keep else pristine.read(info.filename)
        out.writestr(info, data)
    out.close()
    patched.close()
    pristine.close()
    shutil.move(f'{file_path}.new', file_path)
    os.remove(f'{file_path}.pristine')


blob_fixups: blob_fixups_user_type = {
    'system/lib64/libgui-xiaomi.so': blob_fixup()
        .replace_needed(
            'android.hardware.graphics.common-V6-ndk.so',
            'android.hardware.graphics.common-V7-ndk.so',
        ),
    (
        'system/lib64/libcamera_algoup_jni.xiaomi.so',
        'system/lib64/libcamera_mianode_jni.xiaomi.so',
    ): blob_fixup()
        .replace_needed(
            'libgui.so',
            'libgui-xiaomi.so',
        ),
    'system/priv-app/MiuiCamera/MiuiCamera.apk': blob_fixup()
        .call(save_pristine_apk_impl)
        .apktool_unpack('patches')
        .patch_dir('patches')
        .apktool_pack()
        .call(restore_pristine_resources_impl),
}

module = ExtractUtilsModule(
    'camera',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
